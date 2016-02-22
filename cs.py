import os
import sys
import re
import Queue
from threading import Thread
import logging
from tqdm import tqdm


logging.basicConfig(filename='changeString.log', level=logging.INFO)

IGNORE_DIRS = ['.hg', '.gitignore']
# PATTERN = '1.0.3-mapr-5.1.0-SNAPSHOT'
# REPLACE = '1.0.3-mapr-5.2.0-SNAPSHOT'
PATTERN = 'MAPR_JAR_VERSION_NEW'
REPLACE = 'MAPR_JAR_VERSION_NEW_NEW'


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
	for x in range(4):
		worker = replaceWorker(queue)
		worker.daemon = True
		worker.start()

	for root, subFolders, files in os.walk(rootDir):
		for ignoreDir in IGNORE_DIRS:
			if ignoreDir in subFolders:
				subFolders.remove(ignoreDir)
		# pbar = tqdm(files, desc='Processing %s' % root, disable=False)
		for fileName in files:
			# pbar.update(1)
			queue.put((os.path.join(root, fileName), PATTERN, REPLACE))
			# subsMade = doReplace(os.path.join(root, fileName), PATTERN, REPLACE)
			# if subsMade > 0:
			# 	filesChanged += 1
			# 	totalLinesChanged += subsMade

			queue.join()
	return filesChanged, totalLinesChanged

numFilesChanged, numTotalLinesChanged = walkDirectories(os.getcwd())
print 'Total files changed: %s' % numFilesChanged
print 'Total lines changed: %s' % numTotalLinesChanged
