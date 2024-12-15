import os
from sys import exit
from time import time
os.chdir(os.path.abspath(os.path.dirname(__file__)))
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = (-1)


class HashMerge:
	def __init__(self:object, basicsFilePath:str = "title.basics.tsv", akasFilePath:str = "title.akas.tsv", outputFilePath:str = None) -> object:
		self.__basicsFilePath = basicsFilePath if isinstance(basicsFilePath, str) else "title.basics.tsv"
		self.__basicsFilePointer = None
		self.__akasFilePath = akasFilePath if isinstance(akasFilePath, str) else "title.akas.tsv"
		self.__akasFilePointer = None
		self.__drivenByTheSmallerOne = None
		self.__outputFilePath = outputFilePath if isinstance(outputFilePath, str) else None
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
		return bRet
	def initialize(self:object, drivenByTheSmallerOne:bool = True) -> bool:
		try:
			self.__basicsFilePointer = open(self.__basicsFilePath, "rb")
			self.__basicsFilePointer.readline()
			self.__akasFilePointer = open(self.__akasFilePath, "rb")
			self.__akasFilePointer.readline()
			self.__drivenByTheSmallerOne = bool(drivenByTheSmallerOne)
			if self.__outputFilePath is None:
				self.__outputFilePath = "output.hashMergeSD.tsv" if self.__drivenByTheSmallerOne else "output.hashMergeLD.tsv"
			self.__outputFilePointer = open(self.__outputFilePath, "wb")
			self.__outputFilePointer.write(b"titleId\tprimaryTitle\ttitle (regions)\n")
			self.__flag = True
		except BaseException as e:
			self.__closeAll()
			self.__flag = False
			print("Failed to initialize. Details are as follows. \n{0}".format(e))
		return self.__flag
	def __readBasicsFile(self:object) -> tuple:
		if self.__basicsFilePointer is None:
			return (None, None)
		try:
			basicsLine = self.__basicsFilePointer.readline()
			if basicsLine:
				basicsItems = basicsLine.split(b"\t")
				return (basicsItems[0], basicsItems[2])
		except BaseException as e:
			print("Failed to read a line from \"{0}\". Details are as follows. The file will be closed soon. \n{1}".format(self.__basicsFilePath, e))
		self.__close(self.__basicsFilePointer, self.__basicsFilePath)
		self.__basicsFilePointer = None
		return (None, None)
	def __readAkasFile(self:object) -> tuple:
		if self.__akasFilePointer is None:
			return (None, None, None)
		try:
			akasLine = self.__akasFilePointer.readline()
			if akasLine:
				akasItems = akasLine.split(b"\t")
				return (akasItems[0], akasItems[2], akasItems[3])
		except BaseException as e:
			print("Failed to read a line from \"{0}\". Details are as follows. The file will be closed soon. \n{1}".format(self.__akasFilePath, e))
		self.__close(self.__akasFilePointer, self.__akasFilePath)
		self.__akasFilePointer = None
		return (None, None, None)
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
			return False
		
		# Preparation #
		cnt, d, write = 0, {}, self.__write
		
		# Main Algorithm #
		print("Start to perform the \"hash merge\" operation driven by the {0} database. ".format("smaller" if self.__drivenByTheSmallerOne else "larger"))
		startTime = time()
		m0, m1 = self.__readBasicsFile()
		n0, n1, n2 = self.__readAkasFile()
		
		if self.__drivenByTheSmallerOne: # use the smaller one to drive the larger one
			# Hash Table Building #
			while m0: # self.__basicsFilePointer
				d[m0] = [m1, {}] # {"titleId":["primaryTitle", {"title":{"region"}}]
				m0, m1 = self.__readBasicsFile()
			timeDelta = time() - startTime
			print("Finish reading \"{0}\" in {1:.3f} second(s). ".format(self.__basicsFilePath, timeDelta))
			
			# Hash Table Probing #
			identifier = n0
			while n0: # self.__akasFilePointer
				if n0 in d:
					if n1 in d[n0][1]: # d[n0][1].setdefault(n1, set())
						if n2 not in d[n0][1][n1]: # d[n0][1][n1].add(n2)
							d[n0][1][n1].append(n2)
					else:
						d[n0][1][n1] = [n2]
				else:
					d[n0] = [b"", {n1:[n2]}]
				if identifier != n0:
					cnt += write(identifier, d[identifier][0], d[identifier][1])
					if not cnt % 1000000:
						timeDelta = time() - startTime
						print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(cnt, self.__outputFilePath, timeDelta, cnt / timeDelta))
					del d[identifier] # remove records in both tables
					identifier = n0
				n0, n1, n2 = self.__readAkasFile()
			print("Finish reading \"{0}\". ".format(self.__akasFilePath))
			
			# Remaining #
			for identifier in d.keys():
				cnt += write(identifier, d[identifier][0], d[identifier][1])
				if not cnt % 1000000:
					timeDelta = time() - startTime
					print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(cnt, self.__outputFilePath, timeDelta, cnt / timeDelta))
		else: # use the larger one to drive the smaller one
			# Hash Table Building #
			while n0: # self.__akasFilePointer
				if n0 in d: # {"titleId":{"title":{"region"}}}
					if n1 in d[n0]: # d[n0].setdefault(n1, set())
						if n2 not in d[n0][n1]: # d[n0][n1].add(n2)
							d[n0][n1].append(n2)
					else:
						d[n0][n1] = [n2]
				else:
					d[n0] = {n1:[n2]}
				n0, n1, n2 = self.__readAkasFile()
			timeDelta = time() - startTime
			print("Finish reading \"{0}\" in {1:.3f} second(s). ".format(self.__akasFilePath, timeDelta))
			
			# Hash Table Probing #
			while m0: # self.__basicsFilePointer
				if m0 in d:
					cnt += write(m0, m1, d[m0])
					if not cnt % 1000000:
						timeDelta = time() - startTime
						print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(cnt, self.__outputFilePath, timeDelta, cnt / timeDelta))
					del d[m0] # remove records in both tables
				else:
					cnt += write(m0, m1)
					if not cnt % 1000000:
						timeDelta = time() - startTime
						print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(cnt, self.__outputFilePath, timeDelta, cnt / timeDelta))
				m0, m1 = self.__readBasicsFile()
			print("Finish reading \"{0}\". ".format(self.__basicsFilePath))
			
			# Remaining #
			for identifier in d.keys():
				cnt += write(identifier, b"", d[identifier])
				if not cnt % 1000000:
					timeDelta = time() - startTime
					print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(cnt, self.__outputFilePath, timeDelta, cnt / timeDelta))
		
		# File Closing and Performance #
		self.__close(self.__outputFilePointer, self.__outputFilePath)
		timeDelta = time() - startTime
		self.__outputFilePointer = None
		print("Finish performing the \"hash merge\" operation with {0} datum lines written in {1:.3f} second(s) at {2:.3f} datum/s. ".format(cnt, timeDelta, cnt / timeDelta))
		
		# Cleaning #
		self.__flag = False
		return cnt

	
def main() -> int:
	hashMerge = HashMerge()
	if hashMerge.initialize():
		iRet = EXIT_SUCCESS if hashMerge.merge() else EXIT_FAILURE
	else:
		iRet = EOF
	print("Please press the enter key to exit. ")
	input()
	return iRet



if __name__ == "__main__":
	exit(main())