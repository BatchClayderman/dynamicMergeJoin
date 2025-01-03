import os
from sys import exit
from time import time
os.chdir(os.path.abspath(os.path.dirname(__file__)))
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class MergeMerge:
	def __init__(self:object, basicsFilePath:str = "title.basics.tsv", akasFilePath:str = "title.akas.tsv", outputFilePath:str = "output.mergeMerge.tsv") -> object:
		self.__basicsFilePath = basicsFilePath if isinstance(basicsFilePath, str) else "title.basics.tsv"
		self.__basicsFilePointer = None
		self.__akasFilePath = akasFilePath if isinstance(akasFilePath, str) else "title.akas.tsv"
		self.__akasFilePointer = None
		self.__outputFilePath = outputFilePath if isinstance(outputFilePath, str) else "output.mergeMerge.tsv"
		self.__outputFilePointer = None
		self.__flag = False
	def __close(self:object, filePointer:object, filePath:str = None) -> bool:
		try:
			filePointer.close()
			return True
		except BaseException:
			if isinstance(filePath, str) and filePath:
				print("Failed to close \"{0}\". Exceptions are as follows. \n{1}".format(filePath, e))
			return False
	def __closeAll(self:object) -> bool:
		bRet = all([self.__close(self.__basicsFilePointer), self.__close(self.__akasFilePointer), self.__close(self.__outputFilePointer)])
		self.__basicsFilePointer = self.__akasFilePointer = self.__outputFilePointer = None
		self.__inputFilePointerCount = 0
		return bRet
	def initialize(self:object) -> bool:
		try:
			self.__basicsFilePointer = open(self.__basicsFilePath, "rb")
			self.__basicsFilePointer.readline()
			self.__akasFilePointer = open(self.__akasFilePath, "rb")
			self.__akasFilePointer.readline()
			self.__outputFilePointer = open(self.__outputFilePath, "wb")
			self.__outputFilePointer.write(b"titleId\tprimaryTitle\ttitle (regions)\n")
			self.__inputFilePointerCount = 2
			self.__flag = True
		except BaseException as e:
			self.__closeAll()
			self.__flag = False
			print("Failed to initialize. Details are as follows. \n{0}".format(e))
		return self.__flag
	def __readBasicsFile(self:object) -> tuple:
		if self.__basicsFilePointer is None:
			return (b"z", b"z")
		try:
			basicsLine = self.__basicsFilePointer.readline()
			if basicsLine:
				basicsItems = basicsLine.split(b"\t")
				return (basicsItems[0], basicsItems[2])
			else:
				print("Finish reading \"{0}\". ".format(self.__basicsFilePath))
		except BaseException as e:
			print("Failed to read a line from \"{0}\". Details are as follows. The file will be closed soon. \n{1}".format(self.__basicsFilePath, e))
		self.__close(self.__basicsFilePointer, self.__basicsFilePath)
		self.__basicsFilePointer = None
		self.__inputFilePointerCount -= 1
		return (b"z", b"z")
	def __readAkasFile(self:object) -> tuple:
		if self.__akasFilePointer is None:
			return (b"z", b"z", b"z")
		try:
			akasLine = self.__akasFilePointer.readline()
			if akasLine:
				akasItems = akasLine.split(b"\t")
				return (akasItems[0], akasItems[2], akasItems[3])
			else:
				print("Finish reading \"{0}\". ".format(self.__akasFilePath))
		except BaseException as e:
			print("Failed to read a line from \"{0}\". Details are as follows. The file will be closed soon. \n{1}".format(self.__akasFilePath, e))
		self.__close(self.__akasFilePointer, self.__akasFilePath)
		self.__akasFilePointer = None
		self.__inputFilePointerCount -= 1
		return (b"z", b"z", b"z")
	def __write(self:object, identifier:bytes, primaryTitle:bytes, d:dict = {}) -> int:
		toWrite = identifier + b"\t" +primaryTitle
		if d:
			for key, values in d.items():
				toWrite += b"\t" + key + b" (" + b",".join(values) + b")"
		else:
			toWrite += b"\t"
		toWrite += b"\n" # "{0}\t{1}\t{2}\n".format(titleId, primaryTitle, b"\t".join([b"{0} ({1})".format(key, b",".join(value)) for key, value in title.items()])
		try:
			self.__outputFilePointer.write(toWrite)
			self.__outputFilePointer.flush()
			return 1
		except BaseException as e:
			print("Failed to write the following binary strings to \"{0}\". \n{1}\nDetails are as follows. \n{2}".format(self.__outputFilePath, toWrite, e))
			return 0
	def merge(self:object) -> int:
		# Status Checking #
		if not self.__flag:
			print("Please call ``initialize`` before calling ``merge``. ")
			return 0
		
		# Preparation #
		cnt, primaryTitle, titles = 0, b"", {}
		
		# Main Algorithm #
		print("Start to perform the \"merge merge\" operation. ")
		startTime = time()
		m0, m1 = self.__readBasicsFile()
		n0, n1, n2 = self.__readAkasFile()
		while self.__inputFilePointerCount:
			# Identifier Getting #
			titleId = min(m0, n0) # merge
			
			# Left #
			while m0 == titleId:
				primaryTitle = m1
				# input(str({"m0":m0, "m1":m1})) # debug
				m0, m1 = self.__readBasicsFile()
			
			# Right #
			while n0 == titleId:
				if n1 in titles: # titles.setdefault(n1, set())
					if n2 not in titles[n1]: # titles[n1].add(n2)
						titles[n1].append(n2)
				else:
					titles[n1] = [n2]
				# input(str({"n0":n0, "n1":n1, "n2":n2})) # debug
				n0, n1, n2 = self.__readAkasFile()
			
			# Next #
			cnt += self.__write(titleId, primaryTitle, titles)
			if not cnt % 1000000:
				timeDelta = time() - startTime
				print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(cnt, self.__outputFilePath, timeDelta, cnt / timeDelta))
			primaryTitle = b""
			titles.clear()
		
		# File Closing and Performance #
		self.__close(self.__outputFilePointer)
		timeDelta = time() - startTime
		self.__outputFilePointer = None
		print("Finish performing the \"merge merge\" operation with {0} datum lines written in {1:.3f} second(s) at {2:.3f} datum/s. ".format(cnt, timeDelta, cnt / timeDelta))
		
		# Cleaning #
		self.__flag = False
		return cnt

	
def main() -> int:
	mergeMerge = MergeMerge()
	if mergeMerge.initialize():
		iRet = EXIT_SUCCESS if mergeMerge.merge() else EXIT_FAILURE
	else:
		iRet = EOF
	print("Please press the enter key to exit. ")
	input()
	return iRet



if __name__ == "__main__":
	exit(main())