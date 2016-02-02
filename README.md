# AndroidMethodsCounter
This python tool can be used to get the count of methods, as well as the count of lines and classes, in android project.

## Description
1. This tool counts all implemented methods in public classes, inner classes, anonymous inner classes, abstract classes and enums. But the methods that not implemented in abstract class or interface are not counted.
2. The comments and blank lines in codes are counted to the number of lines. Because they are also important parts in the codes.

## Usage
There are two files in AndroidMethodsCounter.

config.ini is the configuration file. You should edit the file to specify some configurations.

The "ProjectDir" option should be set as the path of which project you want to count.

The "ShowSingleFile" option controls whether single file statistics is shown or not in the log file. 'true' means show, and 'false' means not show, apparently.

After configured finished, run the MethodsCounter.py and you will get log to show the statistics.

## Attentions
The counted number of methods may be not entirely accurate. You should not rely on this tool at academic or commercial scenes. In most cases, it works fine. But in some special cases, the count may be more or less than the actual count.
This is because the AndroidMethodsCounter is a lightweight tool. We do not use the lexical analysis for the java codes. Only some string regulations are applied for detection of comments, classes and methods. It cannot be entirely accurate.
