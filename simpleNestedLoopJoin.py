import os
from sys import exit
from time import time
os.chdir(os.path.abspath(os.path.dirname(__file__)))
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class SimpleNestedLoopJoin:
	def __init__(self:object, basicsFilePath:str = "title.basics.tsv", akasFilePath:str = "title.akas.tsv", outputFilePath:str = "output.simpleNestedLoopJoin.tsv") -> object:
		self.__basicsFilePath = basicsFilePath if isinstance(basicsFilePath, str) else "title.basics.tsv"
		self.__basicsFilePointer = None
		self.__akasFilePath = akasFilePath if isinstance(akasFilePath, str) else "title.akas.tsv"
		self.__akasFilePointer = None
		self.__outputFilePath = outputFilePath if isinstance(outputFilePath, str) else "output.simpleNestedLoopJoin.tsv"
		self.__outputFilePointer = None
		self.__flag = False
	def __closeOutputFilePointer(self:object) -> bool:
		try:
			self.__outputFilePointer.close()
			return True
		except BaseException:
			print("Failed to close \"{0}\". Exceptions are as follows. \n{1}".format(self.__outputFilePath, e))
			return False
	def initialize(self:object) -> bool:
		try:
			self.__outputFilePointer = open(self.__outputFilePath, "wb")
			self.__outputFilePointer.write(b"titleId\tprimaryTitle\ttitle (regions)\n")
			self.__flag = True
		except BaseException as e:
			self.__closeOutputFilePointer()
			self.__outputFilePointer = None
			self.__flag = False
			print("Failed to initialize. Details are as follows. \n{0}".format(e))
		return self.__flag
	def __write(self:object, identifier:bytes, primaryTitle:bytes, d:dict = {}) -> int:
		toWrite = identifier + b"\t" +primaryTitle
		for key, values in d.items():
			toWrite += b"\t" + key + b" (" + b",".join(values) + b")"
		toWrite += b"\n" # "{0}\t{1}\t{2}\n".format(titleId, primaryTitle, b"\t".join([b"{0} ({1})".format(key, b",".join(value)) for key, value in title.items()])
		try:
			self.__outputFilePointer.write(toWrite)
			self.__outputFilePointer.flush()
			return 1
		except BaseException as e:
			print("Failed to write the following binary strings to \"{0}\". \n{1}\nDetails are as follows. \n{2}".format(self.__outputFilePath, toWrite, e))
			return 0
	def join(self:object) -> int:
		# Status Checking #
		if not self.__flag:
			print("Please call ``initialize`` before calling ``join``. ")
			return False
		
		# Preparation #
		cnt = 0
		
		# Main Algorithm #
		print("Start to perform the \"simple nested loop join (SNLJ)\" operation. It may take a long time. ")
		print("Please use \"Ctrl + C\" to break the algorithm and estimate the total time manually if it is necessary. ")
		startTime = time()
		try:
			# basics -> akas #
			with open(self.__basicsFilePath, "rb") as basicsPointer:
				basicsPointer.readline()
				basicsLine = basicsPointer.readline()
				while basicsLine:
					basicsItems = basicsLine.split(b"\t")
					titleId, primaryTitle, titles = basicsItems[0], basicsItems[2], {}
					with open(self.__akasFilePath, "rb") as akasPointer:
						akasPointer.readline()
						akasLine = akasPointer.readline()
						while akasLine:
							akasItems = akasLine.split(b"\t")
							if akasItems[0] == titleId:
								title, region = akasItems[2], akasItems[3]
								titles.setdefault(title, [])
								if region not in titles[title]:
									titles[title].append(region)
							akasLine = akasPointer.readline()
					cnt += self.__write(titleId, primaryTitle, titles)
					basicsLine = basicsPointer.readline()
		except KeyboardInterrupt:
			print("The main algorithm is interrupted by users. ")
		except BaseException as e:
			print("Exceptions occurred during the main algorithm. Details are as follows. \n{0}".format(e))
		
		# File Closing and Performance #
		self.__closeOutputFilePointer()
		self.__outputFilePointer = None
		timeDelta = time() - startTime
		print("Finish performing the \"simple nested loop join (SNLJ)\" operation with {0} datum lines written in {1:.3f} second(s) at {2:.3f} datum/s. ".format(cnt, timeDelta, cnt / timeDelta))
		
		# Cleaning #
		self.__flag = False
		return cnt

	
def main() -> int:
	simpleNestedLoopJoin = SimpleNestedLoopJoin()
	if simpleNestedLoopJoin.initialize():
		iRet = EXIT_SUCCESS if simpleNestedLoopJoin.join() else EXIT_FAILURE
	else:
		iRet = EOF
	print("Please press the enter key to exit. ")
	input()
	return iRet



if __name__ == "__main__":
	exit(main())