-- Update employees with correct Crossmark API IDs
UPDATE employees SET external_id = '19461' WHERE name = 'DIANE CARR';
UPDATE employees SET external_id = '70712' WHERE name = 'MICHELLE MONTAGUE';
UPDATE employees SET external_id = '83253' WHERE name = 'THOMAS RARICK';
UPDATE employees SET external_id = '141359' WHERE name = 'NANCY DINKINS';
UPDATE employees SET external_id = '154619' WHERE name = 'MAXX SPALLONE';
UPDATE employees SET external_id = '140433' WHERE name = 'LANIE SULLIVAN';
UPDATE employees SET external_id = '125588' WHERE name = 'ROBI DUNFEE';
UPDATE employees SET external_id = '89095' WHERE name = 'DENISE HEYEN';
UPDATE employees SET external_id = '157573' WHERE name = 'CODY WEAVER';
UPDATE employees SET external_id = '157586' WHERE name = 'ARIANA FAULKNER';
UPDATE employees SET external_id = '157632' WHERE name = 'BRANDY CREASEY';
UPDATE employees SET external_id = '145851' WHERE name = 'KAREN MCCULLOUGH COLLIER';

-- Verify updates
SELECT id, name, external_id FROM employees WHERE external_id IS NOT NULL;