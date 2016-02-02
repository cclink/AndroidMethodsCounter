#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import ConfigParser
import xml.dom.minidom
import codecs
import re
from exceptions import RuntimeError
import time

# Get a config parse
def getConfigParser():
    configFile = os.path.join(os.path.dirname(__file__), 'config.ini')
    if os.path.exists(configFile):
        parser = ConfigParser.ConfigParser()
        parser.read(configFile)
        return parser

# Check whether the project is an Eclipse project
def isEclipseProject(projectDir):
    manifestFile = os.path.join(projectDir, 'AndroidManifest.xml')
    return os.path.exists(manifestFile)

# Check whether the project is an Android Studio project
def isAndroidStudioProject(projectDir):
    manifestFile = os.path.join(projectDir, 'AndroidManifest.xml')
    gradleFile = os.path.join(projectDir, 'build.gradle')
    if os.path.exists(manifestFile):
        return False
    else:
        return os.path.exists(gradleFile)

# Get the source code folder path
def getSrcPathList(isEclipse, projectDir):
    srcPath = []
    if isEclipse:
        cfgFile = os.path.join(projectDir, '.classpath')
        if os.path.exists(cfgFile):
            dom = xml.dom.minidom.parse(cfgFile)
            root = dom.documentElement
            items = root.getElementsByTagName('classpathentry')
            for item in items:
                itemKind = item.getAttribute('kind')
                if itemKind == 'src':
                    itemPath = item.getAttribute('path')
                    if itemPath != 'gen':
                        srcPath.append(os.path.join(projectDir, itemPath))
            return srcPath
        else:
            srcPath.append(os.path.join(projectDir, 'src'))
            return srcPath
    else:
        cfgFile = os.path.join(projectDir, 'build.gradle')
        if os.path.exists(cfgFile):
            cfgFp = open(cfgFile, 'r')
            inSourceSetsCfg = False
            braceCount = 0
            for cfgLine in cfgFp:
                stripLine = cfgLine.strip()
                if stripLine.startswith('sourceSets'):
                    inSourceSetsCfg = True
                if inSourceSetsCfg:
                    pos = stripLine.find('java.srcDirs')
                    if pos != -1:
                        stripLine = stripLine[pos + len('java.srcDirs'):].lstrip()
                        assert len(stripLine) > 2
                        if stripLine[0:2] == '+=':
                            temp = os.path.join(projectDir, 'src' + os.path.sep + 'main' + os.path.sep + 'java')
                            srcPath.append(temp)
                            stripLine = stripLine[2:]
                        stripLine = stripLine.lstrip(' [=').rstrip(']')
                        splitLine = stripLine.split(',')
                        for splitItem in splitLine:
                            splitItem = splitItem.strip(' \'"')
                            if len(splitItem) != 0:
                                if os.path.sep != '/':
                                    splitItem = splitItem.replace('/', os.path.sep)
                                elif os.path.sep != '\\':
                                    splitItem = splitItem.replace('\\', os.path.sep)
                                srcPath.append(os.path.join(projectDir, splitItem))
                        break
                    braceCount += stripLine.count('{')
                    braceCount -= stripLine.count('}')
                    if braceCount <= 0:
                        break
            if len(srcPath) == 0:
                srcPath.append(os.path.join(projectDir, 'src' + os.path.sep + 'main' + os.path.sep + 'java'))
            return srcPath
        else:
            srcPath.append(os.path.join(projectDir, 'src' + os.path.sep + 'main' + os.path.sep + 'java'))
            return srcPath


def countMethods(srcPathList):
    srcCountList = []

    classLineRegex = re.compile(r'enum\s+\S+.*?\{|class\s+\S+.*?\{|new\s+\S+\s*\(.*\)\s*\{')
    # Iterate through all source code folders
    for srcPath in srcPathList:
        for (parent, _, fileNames) in os.walk(srcPath):
            for fileName in fileNames:
                # ignores non java code
                if not fileName.endswith('.java'):
                    continue
                # read java code to find used resource
                fileFullPath = os.path.join(parent, fileName)
                fp = open(fileFullPath, 'r')
                fileContent = fp.readlines()
                fp.close()
                lineCount = len(fileContent)
                braceStack = []
                currentBraceCount = 0
                classCount = 0
                methodCount = 0
                for fileLine in fileContent:
                    ret = classLineRegex.search(fileLine)
                    while ret:
                        group0 = ret.group(0)
                        group0Pos = fileLine.find(group0)
                        group0Left = fileLine[0:group0Pos]
                        group0Right = fileLine[group0Pos+len(group0):]
                        for ch in group0Left:
                            if ch == '{':
                                currentBraceCount += 1
                            elif ch == '}':
                                currentBraceCount -= 1
                                if currentBraceCount == 1:
                                    methodCount += 1
                                elif currentBraceCount == 0:
                                    if len(braceStack) != 0:
                                        currentBraceCount = braceStack.pop()
                        fileLine = group0Right
                        ret = classLineRegex.search(fileLine)
                        if currentBraceCount != 0:
                            braceStack.append(currentBraceCount)
                        currentBraceCount = 1
                        classCount += 1
                    for ch in fileLine:
                        if ch == '{':
                            currentBraceCount += 1
                        elif ch == '}':
                            currentBraceCount -= 1
                            if currentBraceCount == 1:
                                methodCount += 1
                            elif currentBraceCount == 0:
                                if len(braceStack) != 0:
                                    currentBraceCount = braceStack.pop()
                fileRelativePath = fileFullPath[len(srcPath):]
                srcCountList.append((fileRelativePath, lineCount, classCount, methodCount))
    return srcCountList

def getReadableTime():
    curTime = time.localtime()
    year = curTime[0]
    month = curTime[1]
    day = curTime[2]
    hour = curTime[3]
    minute = curTime[4]
    second = curTime[5]
    readableTime = '%d-%d-%d %d:%d:%d' % (year, month, day, hour, minute, second)
    return readableTime

def process():
    configParser = getConfigParser()
    if configParser is None:
        return
    # Get the configurations
    projectDir = configParser.get('Dir', 'ProjectDir')

    # project dir is not exist, raise exception
    if not os.path.exists(projectDir):
        raise RuntimeError('Invalid project directory')
    # Check whether the project is Eclipse or Android Studio
    isEclipse = isEclipseProject(projectDir)
    isAndroidStudio = isAndroidStudioProject(projectDir)
    # not Eclipse project，and not Android Studio project, raise exception
    if not isEclipse and not isAndroidStudio:
        raise RuntimeError('Unknown project type')

    # get the source code folder in the project
    srcPathList = getSrcPathList(isEclipse, projectDir)
    for srcPath in srcPathList:
        if not os.path.exists(srcPath):
            raise RuntimeError('Cannot find src path ' + srcPath)

    logContent.append('Project dir: ' + projectDir)

    # get configed resource
    srcCountList = countMethods(srcPathList)
    totalLineCount = 0
    totalClassCount = 0
    totalMethodCount = 0
    for (srcFile, lineCount, classCount, methodCount) in srcCountList:
        logContent.append('%s: %d %d %d' % (srcFile, lineCount, classCount, methodCount))
        totalLineCount += lineCount
        totalClassCount += classCount
        totalMethodCount += methodCount
    logContent.append('Total File Count: %d' % len(srcCountList))
    logContent.append('Total Line Count: %d' % totalLineCount)
    logContent.append('Total Class Count: %d' % totalClassCount)
    logContent.append('Total Method Count: %d' % totalMethodCount)

def saveToLog():
    logFile = 'AndroidMethodsCounter.log'
    # log file exists and not empty, open file with append mode
    if os.path.exists(logFile) and os.path.getsize(logFile) != 0:
        logFp = open(logFile, 'a+')
        logFp.write('\n')   # 追加模式下需要一个额外的换行，和上方的log分隔开
        logFp.writelines([i + '\n' for i in logContent])
    # log file does not exist or empty, open file with write mode
    else:
        logFp = open(logFile, 'w+')
        logFp.writelines([i + '\n' for i in logContent])
    logFp.close()

if __name__ == '__main__':
    logContent = []
    try:
        # start clean process
        logContent.append('------------------------------ ' + getReadableTime() + ' ------------------------------')
        process()
    except Exception, e:
        # append the exception message to log
        logContent.append(e.message)
    finally:
        # save log to file
        saveToLog()
        print 'done'
