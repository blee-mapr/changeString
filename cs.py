#!/usr/bin/python

import os
import sys
import re
import Queue
from threading import Thread
import logging
import xmltodict
from tqdm import tqdm

logging.basicConfig(filename='changeString.log', level=logging.INFO)
IGNORE_DIRS = ['.hg', '.git']


class replaceWorker(Thread):
	def __init__(self, queue):
		Thread.__init__(self)
		self.queue = queue

	def run(self):
		while True:
			fileName, pattern, replace = self.queue.get()
			subsMade = doReplace(fileName, pattern, replace)
			self.queue.task_done()


def doReplace(fileName, pattern, replace):
	totalSubs = 0
	with open(fileName, 'r') as sources:
		lines = sources.readlines()
	with open(fileName, 'w') as sources:
		for line in lines:
			newline, subsMade = re.subn(pattern, replace, line)
			if subsMade > 0:
				logging.info('File: %s' % fileName)
				logging.info('--- %s', line.rstrip('\r\n'))
				logging.info('+++ %s', newline.rstrip('\r\n'))
				totalSubs += subsMade
			sources.write(re.sub(pattern, replace, line))
	return totalSubs


def walkDirectories(rootDir):
	logging.info('Walking %s' % rootDir)
	filesChanged = 0
	totalLinesChanged = 0

	# Create queue and worker threads
	queue = Queue.Queue()
	for x in range(1):
		worker = replaceWorker(queue)
		worker.daemon = True
		worker.start()

	for root, subFolders, files in os.walk(rootDir):
		pbar = tqdm(files, desc='Processing %s' % root, disable=True)
		for ignoreDir in IGNORE_DIRS:
			if ignoreDir in subFolders:
				subFolders.remove(ignoreDir)
		for fileName in files:
			pbar.update(1)
			if fileName.endswith('xml'):
				print('Processing %s' % fileName)
				queue.put((os.path.join(root, fileName), PATTERN, REPLACE))
			else:
				continue
			# subsMade = doReplace(os.path.join(root, fileName), PATTERN, REPLACE)
			# if subsMade > 0:
			# 	filesChanged += 1
			# 	totalLinesChanged += subsMade

		queue.join()
	return filesChanged, totalLinesChanged


def getNewVersionString(version, ecoNumber):
	newVersionString = ''
	tokens = version.split('-')
	if 'SNAPSHOT' in tokens[-1]:
		tokens[-1] = ecoNumber
		newVersionString = '-'.join(tokens)
	elif len(tokens) == 1:
		newVersionString = tokens[0] + '-mapr-%s' % ecoNumber
	elif (len(tokens) == 2) & ('mapr' in tokens[1]):
		tokens.append(ecoNumber)
		newVersionString = '-'.join(tokens)

	return newVersionString


def readPom():
	try:
		os.chdir(os.getcwd())
		with open('pom.xml', 'r') as fh:
			pomData = fh.read()
		result = xmltodict.parse(pomData)
		version = result['project']['version']
		return version
	except Exception, e:
		print e
		print 'Cannot find pom.xml'
		return False
	return True


def main():
	global PATTERN, REPLACE
	if len(sys.argv) == 1:
		print 'No arguments'
	elif len(sys.argv) > 1:
		PATTERN = sys.argv[1]
		REPLACE = sys.argv[2]

	print 'Performing search in %s' % os.getcwd()
	if len(sys.argv) <= 1:
		try:
			version = readPom()
			if version is False:
				return 1
		except Exception, e:
			print e
			return 1
		print 'Current version is %s' % version
		newVersion = getNewVersionString(version, '1710')
		print 'New version can be %s' % newVersion
		userInput = raw_input('Continue (y/n)?')
		if userInput[0].lower() == 'n':
			sys.exit(0)
		else:
			PATTERN = version
			REPLACE = newVersion
			print 'go!'

	print 'Replacing all instances of %s with %s' % (PATTERN, REPLACE)
	numFilesChanged, numTotalLinesChanged = walkDirectories(os.getcwd())
	# print 'Total files changed: %s' % numFilesChanged
	# print 'Total lines changed: %s' % numTotalLinesChanged


if __name__ == "__main__":
	main()
