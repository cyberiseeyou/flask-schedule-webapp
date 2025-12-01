#!/bin/bash

###############################################################################
# Flask Schedule Webapp - Database Backup Script
#
# This script provides comprehensive database backup functionality with
# scheduling options for PostgreSQL and SQLite databases.
#
# Usage:
#   ./backup.sh                    - Interactive mode
#   ./backup.sh --now              - Run backup immediately
#   ./backup.sh --schedule         - Set up scheduled backups
#   ./backup.sh --restore <file>   - Restore from backup file
#   ./backup.sh --list             - List available backups
###############################################################################

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default configuration
BACKUP_DIR="${BACKUP_DIR:-./backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DOCKER_DIR="deployment/docker"

# Print functions
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Banner
show_banner() {
    echo -e "${CYAN}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         Flask Schedule Webapp - Database Backup          ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Load environment variables
load_env() {
    if [ -f ".env" ]; then
        source .env 2>/dev/null || true
    fi
}

# Detect database type
detect_database() {
    load_env

    if [ -n "$POSTGRES_DB" ] && docker ps --format '{{.Names}}' 2>/dev/null | grep -q "scheduler-db"; then
        echo "postgresql-docker"
    elif [ -n "$DATABASE_URL" ] && [[ "$DATABASE_URL" == postgresql* ]]; then
        echo "postgresql"
    elif [ -f "instance/scheduler.db" ]; then
        echo "sqlite"
    else
        echo "none"
    fi
}

# Create backup directory
ensure_backup_dir() {
    local dir="$1"
    if [ ! -d "$dir" ]; then
        mkdir -p "$dir"
        print_success "Created backup directory: $dir"
    fi
}

# Generate backup filename with timestamp
generate_backup_name() {
    local db_type="$1"
    local timestamp=$(date +%Y%m%d_%H%M%S)
    echo "scheduler_backup_${db_type}_${timestamp}"
}

# Backup PostgreSQL database (Docker)
backup_postgresql_docker() {
    local backup_dir="$1"
    local backup_name=$(generate_backup_name "postgresql")
    local backup_file="${backup_dir}/${backup_name}.sql.gz"

    print_info "Backing up PostgreSQL database from Docker container..."

    # Get database credentials from environment
    local db_name="${POSTGRES_DB:-crossmark_scheduler}"
    local db_user="${POSTGRES_USER:-scheduler_app}"

    # Perform backup using docker exec
    if docker exec scheduler-db pg_dump -U "$db_user" "$db_name" 2>/dev/null | gzip > "$backup_file"; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup created: $backup_file ($size)"
        echo "$backup_file"
    else
        print_error "Failed to backup PostgreSQL database"
        rm -f "$backup_file"
        return 1
    fi
}

# Backup PostgreSQL database (Native)
backup_postgresql_native() {
    local backup_dir="$1"
    local backup_name=$(generate_backup_name "postgresql")
    local backup_file="${backup_dir}/${backup_name}.sql.gz"

    print_info "Backing up PostgreSQL database..."

    # Parse DATABASE_URL for connection details
    if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        local db_user="${BASH_REMATCH[1]}"
        local db_pass="${BASH_REMATCH[2]}"
        local db_host="${BASH_REMATCH[3]}"
        local db_port="${BASH_REMATCH[4]}"
        local db_name="${BASH_REMATCH[5]}"

        PGPASSWORD="$db_pass" pg_dump -h "$db_host" -p "$db_port" -U "$db_user" "$db_name" | gzip > "$backup_file"

        if [ -f "$backup_file" ] && [ -s "$backup_file" ]; then
            local size=$(du -h "$backup_file" | cut -f1)
            print_success "Backup created: $backup_file ($size)"
            echo "$backup_file"
        else
            print_error "Failed to backup PostgreSQL database"
            rm -f "$backup_file"
            return 1
        fi
    else
        print_error "Could not parse DATABASE_URL"
        return 1
    fi
}

# Backup SQLite database
backup_sqlite() {
    local backup_dir="$1"
    local backup_name=$(generate_backup_name "sqlite")
    local backup_file="${backup_dir}/${backup_name}.db.gz"
    local sqlite_file="instance/scheduler.db"

    print_info "Backing up SQLite database..."

    if [ -f "$sqlite_file" ]; then
        # Use SQLite backup command for consistency
        sqlite3 "$sqlite_file" ".backup '${backup_dir}/${backup_name}.db'" 2>/dev/null || cp "$sqlite_file" "${backup_dir}/${backup_name}.db"
        gzip "${backup_dir}/${backup_name}.db"

        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup created: $backup_file ($size)"
        echo "$backup_file"
    else
        print_error "SQLite database not found: $sqlite_file"
        return 1
    fi
}

# Run backup based on detected database type
run_backup() {
    local backup_dir="${1:-$BACKUP_DIR}"
    ensure_backup_dir "$backup_dir"

    local db_type=$(detect_database)

    case "$db_type" in
        "postgresql-docker")
            backup_postgresql_docker "$backup_dir"
            ;;
        "postgresql")
            backup_postgresql_native "$backup_dir"
            ;;
        "sqlite")
            backup_sqlite "$backup_dir"
            ;;
        "none")
            print_error "No database detected. Please ensure the application is configured."
            return 1
            ;;
        *)
            print_error "Unknown database type: $db_type"
            return 1
            ;;
    esac
}

# Restore from backup
restore_backup() {
    local backup_file="$1"

    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        return 1
    fi

    print_warning "WARNING: This will overwrite the current database!"
    read -p "Are you sure you want to restore from $backup_file? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled"
        return 0
    fi

    local db_type=$(detect_database)

    if [[ "$backup_file" == *.sql.gz ]]; then
        # PostgreSQL restore
        case "$db_type" in
            "postgresql-docker")
                local db_name="${POSTGRES_DB:-crossmark_scheduler}"
                local db_user="${POSTGRES_USER:-scheduler_app}"

                print_info "Restoring PostgreSQL database from Docker container..."
                gunzip -c "$backup_file" | docker exec -i scheduler-db psql -U "$db_user" -d "$db_name"
                print_success "Database restored successfully"
                ;;
            "postgresql")
                if [[ "$DATABASE_URL" =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
                    local db_user="${BASH_REMATCH[1]}"
                    local db_pass="${BASH_REMATCH[2]}"
                    local db_host="${BASH_REMATCH[3]}"
                    local db_port="${BASH_REMATCH[4]}"
                    local db_name="${BASH_REMATCH[5]}"

                    print_info "Restoring PostgreSQL database..."
                    gunzip -c "$backup_file" | PGPASSWORD="$db_pass" psql -h "$db_host" -p "$db_port" -U "$db_user" "$db_name"
                    print_success "Database restored successfully"
                fi
                ;;
        esac
    elif [[ "$backup_file" == *.db.gz ]]; then
        # SQLite restore
        print_info "Restoring SQLite database..."
        gunzip -c "$backup_file" > "instance/scheduler.db"
        print_success "Database restored successfully"
    else
        print_error "Unknown backup format: $backup_file"
        return 1
    fi
}

# List available backups
list_backups() {
    local backup_dir="${1:-$BACKUP_DIR}"

    if [ ! -d "$backup_dir" ]; then
        print_warning "No backup directory found: $backup_dir"
        return 0
    fi

    echo ""
    print_info "Available backups in $backup_dir:"
    echo ""

    local count=0
    for file in "$backup_dir"/*.gz 2>/dev/null; do
        if [ -f "$file" ]; then
            local size=$(du -h "$file" | cut -f1)
            local date=$(stat -c %y "$file" 2>/dev/null | cut -d' ' -f1 || stat -f %Sm -t %Y-%m-%d "$file" 2>/dev/null)
            echo "  - $(basename "$file") ($size) - $date"
            ((count++))
        fi
    done

    if [ $count -eq 0 ]; then
        print_warning "No backups found"
    else
        echo ""
        print_info "Total: $count backup(s)"
    fi
}

# Clean old backups
cleanup_old_backups() {
    local backup_dir="${1:-$BACKUP_DIR}"
    local retention_days="${2:-$RETENTION_DAYS}"

    print_info "Cleaning up backups older than $retention_days days..."

    local deleted=0
    find "$backup_dir" -name "scheduler_backup_*.gz" -mtime +$retention_days -delete 2>/dev/null && deleted=$?

    print_success "Cleanup completed"
}

# Setup scheduled backup using cron
setup_schedule() {
    show_banner

    echo "Configure automated backup schedule"
    echo ""

    # Get backup directory
    read -p "Backup directory [$BACKUP_DIR]: " input_dir
    local backup_dir="${input_dir:-$BACKUP_DIR}"
    ensure_backup_dir "$backup_dir"

    # Get schedule frequency
    echo ""
    echo "Select backup frequency:"
    echo "  1) Daily"
    echo "  2) Every 12 hours"
    echo "  3) Every 6 hours"
    echo "  4) Weekly (Sundays)"
    echo "  5) Custom cron expression"
    echo ""
    read -p "Select option [1-5]: " freq_option

    local cron_schedule
    case "$freq_option" in
        1) cron_schedule="0 2 * * *"   # Daily at 2 AM
           ;;
        2) cron_schedule="0 */12 * * *" # Every 12 hours
           ;;
        3) cron_schedule="0 */6 * * *"  # Every 6 hours
           ;;
        4) cron_schedule="0 2 * * 0"   # Weekly on Sundays at 2 AM
           ;;
        5) read -p "Enter cron expression (e.g., '0 2 * * *'): " cron_schedule
           ;;
        *) cron_schedule="0 2 * * *"   # Default: Daily at 2 AM
           ;;
    esac

    # Get preferred time for scheduled options
    if [[ "$freq_option" =~ ^[1234]$ ]]; then
        read -p "Preferred hour (0-23) [2]: " hour
        hour="${hour:-2}"
        cron_schedule=$(echo "$cron_schedule" | sed "s/^0 [0-9*\/]* /0 $hour /")
    fi

    # Get retention days
    echo ""
    read -p "Keep backups for how many days? [$RETENTION_DAYS]: " retention
    retention="${retention:-$RETENTION_DAYS}"

    # Create the cron job
    local script_path="$(cd "$(dirname "$0")" && pwd)/backup.sh"
    local cron_command="$cron_schedule cd $(pwd) && $script_path --now --dir \"$backup_dir\" --cleanup $retention >> \"$backup_dir/backup.log\" 2>&1"

    echo ""
    print_info "Proposed cron job:"
    echo "  $cron_command"
    echo ""

    read -p "Add this to crontab? (yes/no): " confirm

    if [ "$confirm" = "yes" ]; then
        # Remove existing backup cron jobs for this project
        crontab -l 2>/dev/null | grep -v "$script_path" | crontab - 2>/dev/null || true

        # Add new cron job
        (crontab -l 2>/dev/null; echo "$cron_command") | crontab -

        print_success "Scheduled backup configured!"
        echo ""
        print_info "Schedule: $cron_schedule"
        print_info "Backup directory: $backup_dir"
        print_info "Retention: $retention days"
        echo ""
        print_info "To view scheduled jobs: crontab -l"
        print_info "To remove scheduled backup: crontab -e (and delete the line)"
    else
        print_info "Schedule not added"
    fi
}

# Show interactive menu
show_menu() {
    show_banner

    local db_type=$(detect_database)
    print_info "Detected database: $db_type"
    echo ""

    echo "Select an option:"
    echo "  1) Run backup now"
    echo "  2) Set up scheduled backups"
    echo "  3) Restore from backup"
    echo "  4) List available backups"
    echo "  5) Clean old backups"
    echo "  6) Exit"
    echo ""
    read -p "Select option [1-6]: " option

    case "$option" in
        1)
            echo ""
            read -p "Backup directory [$BACKUP_DIR]: " input_dir
            run_backup "${input_dir:-$BACKUP_DIR}"
            ;;
        2)
            setup_schedule
            ;;
        3)
            echo ""
            list_backups
            echo ""
            read -p "Enter backup file path: " backup_file
            restore_backup "$backup_file"
            ;;
        4)
            list_backups
            ;;
        5)
            echo ""
            read -p "Delete backups older than how many days? [$RETENTION_DAYS]: " days
            cleanup_old_backups "$BACKUP_DIR" "${days:-$RETENTION_DAYS}"
            ;;
        6)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            exit 1
            ;;
    esac
}

# Parse command line arguments
main() {
    load_env

    case "${1:-}" in
        --now)
            shift
            local backup_dir="$BACKUP_DIR"
            local cleanup_days=""

            while [ $# -gt 0 ]; do
                case "$1" in
                    --dir)
                        backup_dir="$2"
                        shift 2
                        ;;
                    --cleanup)
                        cleanup_days="$2"
                        shift 2
                        ;;
                    *)
                        shift
                        ;;
                esac
            done

            run_backup "$backup_dir"

            if [ -n "$cleanup_days" ]; then
                cleanup_old_backups "$backup_dir" "$cleanup_days"
            fi
            ;;
        --schedule)
            setup_schedule
            ;;
        --restore)
            if [ -z "$2" ]; then
                print_error "Please specify backup file: ./backup.sh --restore <file>"
                exit 1
            fi
            restore_backup "$2"
            ;;
        --list)
            list_backups "${2:-$BACKUP_DIR}"
            ;;
        --help|-h)
            echo "Usage: ./backup.sh [option]"
            echo ""
            echo "Options:"
            echo "  (none)              Interactive mode"
            echo "  --now               Run backup immediately"
            echo "    --dir <path>      Backup directory (default: ./backups)"
            echo "    --cleanup <days>  Delete backups older than N days"
            echo "  --schedule          Set up scheduled backups"
            echo "  --restore <file>    Restore from backup file"
            echo "  --list [dir]        List available backups"
            echo "  --help              Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  BACKUP_DIR          Default backup directory (./backups)"
            echo "  RETENTION_DAYS      Default retention period (30 days)"
            ;;
        *)
            show_menu
            ;;
    esac
}

# Run main function
main "$@"
