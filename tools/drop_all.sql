
-- This script drops the COFFEE user and all associated database objects.
-- It is designed to be run by a privileged user (e.g., ADMIN).

-- Exit on first error to prevent partial setup
WHENEVER SQLERROR EXIT SQL.SQLCODE

-- Enable server output to see messages
SET SERVEROUTPUT ON;

DECLARE
    v_user_count NUMBER;
BEGIN
    -- Check if the user 'coffee' exists before trying to drop it
    SELECT COUNT(*) INTO v_user_count FROM dba_users WHERE username = 'COFFEE';
    IF v_user_count > 0 THEN
        -- Kill any active sessions for the user before dropping
        FOR r IN (SELECT sid, serial# FROM v$session WHERE username = 'COFFEE') LOOP
            EXECUTE IMMEDIATE 'ALTER SYSTEM KILL SESSION \'' || TO_CHAR(r.sid) || ',' || TO_CHAR(r.serial#) || '\' IMMEDIATE';
        END LOOP;
        DBMS_OUTPUT.PUT_LINE('User COFFEE exists. Dropping user...');
        EXECUTE IMMEDIATE 'DROP USER coffee CASCADE';
        DBMS_OUTPUT.PUT_LINE('User COFFEE dropped successfully.');
    ELSE
        DBMS_OUTPUT.PUT_LINE('User COFFEE does not exist. Nothing to drop.');
    END IF;
END;
/

PROMPT Database cleanup complete.

EXIT;
