GBot
-------------------------------------------------------------------------------------------------------------------------------------------
Written by Kameron Penn
Inspired by Chris Rose

Store scripts in scripts folder.

Schedule the scripts in the gbt folder with '.gbt' files.

gbt syntax:
format_string ; script_file_name ; notification

format_string:
    yyyy.mm.dd.HH.MM:SS (leave as letters to be variable)

notification:
    0 for nothing
    1 popup display
    2 tray notification

use a # for comments

examples:
    yyyy.mm.dd.HH.MM:01 ; example.cmd ; 1  # run example.cmd on the first second of every minute with a popup notification
    2018.04.03.HH.00:00 ; example.cmd ; 0  # run example.cmd on 4/3/2018 at the start of every hour

