import os
from sys import exit
from json import dumps
from gzip import open as gzipOpen
from time import sleep, time
from copy import deepcopy
os.chdir(os.path.abspath(os.path.dirname(__file__)))
EXIT_SUCCESS = 0
EXIT_FAILURE = 1
EOF = -1


class DebugLevel:
	defaultCharacter = "?"
	defaultName = "*"
	defaultSymbol = "[?]"
	defaultValue = 0
	def __init__(self:object, d:dict) -> object:
		self.character = d["character"] if "character" in d else DebugLevel.defaultCharacter
		self.name = d["name"] if "name" in d else DebugLevel.defaultName
		self.symbol = d["symbol"] if "symbol" in d else DebugLevel.defaultSymbol
		self.value = d["value"] if "value" in d else DebugLevel.defaultValue
	def __eq__(self:object, other:object) -> bool:
		if isinstance(other, DebugLevel):
			return self.value == other.value
		elif isinstance(other, (int, float)):
			return self.value == other
		else:
			return False
	def __ne__(self:object, other:object) -> bool:
		if isinstance(other, DebugLevel):
			return self.value != other.value
		elif isinstance(other, (int, float)):
			return self.value != other
		else:
			return True
	def __lt__(self:object, other:object) -> bool:
		if isinstance(other, DebugLevel):
			return self.value < other.value
		elif isinstance(other, (int, float)):
			return self.value < other
		else:
			raise TypeError("TypeError: '<' not supported between instances of '{0}' and '{1}'".format(type(self), type(other)))
	def __le__(self:object, other:object) -> bool:
		if isinstance(other, DebugLevel):
			return self.value <= other.value
		elif isinstance(other, (int, float)):
			return self.value <= other
		else:
			raise TypeError("TypeError: '<=' not supported between instances of '{0}' and '{1}'".format(type(self), type(other)))
	def __gt__(self:object, other:object) -> bool:
		if isinstance(other, DebugLevel):
			return self.value > other.value
		elif isinstance(other, (int, float)):
			return self.value > other
		else:
			raise TypeError("TypeError: '>' not supported between instances of '{0}' and '{1}'".format(type(self), type(other)))
	def __ge__(self:object, other:object) -> bool:
		if isinstance(other, DebugLevel):
			return self.value >= other.value
		elif isinstance(other, (int, float)):
			return self.value >= other
		else:
			raise TypeError("TypeError: '>=' not supported between instances of '{0}' and '{1}'".format(type(self), type(other)))
	def __str__(self:object) -> str:
		return str(self.symbol)
Prompt = DebugLevel({"character":"P", "name":"Prompt", "symbol":"[P]", "value":100})
Critical = DebugLevel({"character":"C", "name":"Critical", "symbol":"[C]", "value":50})
Error = DebugLevel({"character":"E", "name":"Error", "symbol":"[E]", "value":40})
Warning = DebugLevel({"character":"W", "name":"Warning", "symbol":"[W]", "value":30})
Info = DebugLevel({"character":"I", "name":"Info", "symbol":"[I]", "value":20})
Debug = DebugLevel({"character":"D", "name":"Info", "symbol":"[D]", "value":10})

class VirtualNode:
	def __init__(self:object) -> object:
		self.__nodeID = None
		self.__formatter = b"{0}"
		self.__joiner = b"\t"
		self.__operator = lambda elements:b""
		self.__children = []
	def build(self:object, nodeID:int, d:dict) -> bool:
		if isinstance(nodeID, int) and isinstance(d, dict):
			self.__nodeID = nodeID
			if "formatter" in d and isinstance(d["formatter"], bytes):
				self.__formatter = d["formatter"]
			self.__operator = (lambda elements:self.__formatter % elements) if b"%" in self.__formatter else (lambda elements:self.__formatBytes(self.__formatter, elements))
			if "joiner" in d and isinstance(d["joiner"], bytes):
				self.__joiner = d["joiner"]
			return True
		else:
			return False
	def addChild(self:object, child:object) -> bool:
		if isinstance(child, VirtualNode):
			self.__children.append(child)
			return True
		else:
			return False
	def getDict(self:object) -> dict:
		return {"formatter":str(self.__formatter), "joiner":str(self.__joiner), "children":[child.getDict() for child in self.__children]}
	def getJson(self:object, indent:int|str = "\t") -> str:
		return dumps(self.getDict(), indent = indent if isinstance(indent, (int, str)) else "\t")
	def getJoiner(self:object) -> bytes:
		return self.__joiner
	def getNodeID(self:object) -> int:
		return self.__nodeID
	def getChildNodeIDs(self:object) -> list:
		return [child.getNodeID() for child in self.__children]
	def getChildren(self:object) -> list:
		return self.__children
	def __formatBytes(self:object, formatter:bytes, elements:tuple|list) -> bytes:
		formatterIndex, formatterLength, elementIndex, elementLength, lastIndex, bytesRet = 0, len(formatter), 0, len(elements), 0, b""
		while formatterIndex < formatterLength:
			if formatter[formatterIndex] == 123:
				bytesRet += formatter[lastIndex:formatterIndex]
				if formatterIndex + 1 < formatterLength:
					if formatter[formatterIndex + 1] == 123:
						formatterIndex += 1
						bytesRet += b"{"
					elif formatter[formatterIndex + 1] == 125:
						if elementIndex < 0:
							raise ValueError("cannot switch from manual field specification to automatic field numbering")
						else:
							if elementIndex < elementLength:
								bytesRet += bytes(elements[elementIndex])
							else:
								raise IndexError("Replacement index {0} out of range for positional args tuple".format(elementIndex))
							elementIndex += 1
					else:
						startIndex = formatterIndex + 1
						while formatterIndex + 1 < formatterLength:
							if formatter[formatterIndex + 1] == 123:
								raise ValueError("unexpected \'{\' in field name")
							elif formatter[formatterIndex + 1] == 125:
								key = formatter[startIndex:formatterIndex + 1]
								try:
									eleIndex = int(key)
								except:
									raise KeyError("\'{0}\'".format(key))
								else:
									if elementIndex > 0:
										raise ValueError("cannot switch from automatic field numbering to manual field specification")
									else:
										if eleIndex < elementLength:
											bytesRet += bytes(elements[eleIndex])
										else:
											raise IndexError("Replacement index {0} out of range for positional args tuple".format(eleIndex))
										elementIndex = -1
								finally:
									formatterIndex += 1
									break
							formatterIndex += 1
				else:
					raise ValueError("Single \'{\' encountered in format bytes")
				lastIndex = formatterIndex + 1
			elif formatter[formatterIndex] == 125:
				bytesRet += formatter[lastIndex:formatterIndex]
				if formatterIndex + 1 < formatterLength and formatter[formatterIndex + 1] == 125:
					bytesRet += b"}"
					formatterIndex += 1
				else:
					raise ValueError("Single \'}\' encountered in format bytes")
				lastIndex = formatterIndex + 1
			formatterIndex += 1
		bytesRet += formatter[lastIndex:]
		return bytesRet
	def helpFormat(self:object, elements:tuple|list) -> bytes:
		return self.__operator(elements)
	def __eq__(self:object, nodeID:int) -> bool:
		return nodeID == self.__nodeID
	def __str__(self:object) -> str:
		return self.getJson()

class _RealNode:
	def __init__(self:object, datum:bytes, joiner:bytes, nodeIDs:tuple|list|set, virtualNode:VirtualNode) -> object:
		self.__datum = datum
		self.__joiner = joiner
		self.__children = {nodeID:[] for nodeID in nodeIDs}
		self.__virtualNode = virtualNode
	def addChild(self:object, childNode:object, nodeID:int) -> None:
		self.__children[nodeID].append(childNode)
	def getChildren(self:object, childNodeID:int) -> list:
		return self.__children[childNodeID] # if isinstance(childNodeID, int) and childNodeID in self.__children else []
	def __eq__(self:object, identifier:str) -> bool:
		return identifier == self.__datum
	def __bytes__(self:object) -> bytes:
		return self.__virtualNode.helpFormat((self.__datum, ) + tuple(self.__joiner.join([bytes(child) for child in self.__children[key]]) for key in self.__children.keys()))

class Tree:
	def __init__(self:object) -> object:
		self.__virtualRoot = None
		self.__realRoot = None
		self.__length = 0
	def build(self:object, d:dict) -> int:
		if isinstance(d, dict):
			nodeID = 0
			self.__virtualRoot = VirtualNode()
			self.__virtualRoot.build(nodeID, d)
			if "children" in d:
				queue = [(self.__virtualRoot, child) for child in d["children"]]
				while queue:
					parentNode, currentDict = queue.pop(0)
					nodeID += 1
					currentNode = VirtualNode()
					currentNode.build(nodeID, currentDict)
					parentNode.addChild(currentNode)
					if "children" in currentDict:
						queue.extend([(currentNode, child) for child in currentDict["children"]])
			self.__length = nodeID + 1
			return self.__length
		else:
			return 0
	def getDict(self:object) -> dict:
		return self.__virtualRoot.getDict() if self.__virtualRoot else {}
	def getJson(self:object) -> str:
		return self.__virtualRoot.getJson() if self.__virtualRoot else ""
	def mergeLine(self:object, line:list) -> bool:
		if isinstance(line, (tuple, list)) and line and line[0] == self.__realRoot:
			queue = [(self.__virtualRoot, child, self.__realRoot) for child in self.__virtualRoot.getChildren()]
			while queue:
				parentVirtualNode, currentVirtualNode, parentRealNode = queue.pop(0)
				currentVirtualNodeID = currentVirtualNode.getNodeID()
				if -len(line) <= currentVirtualNodeID < len(line) and line[currentVirtualNodeID] is not None:
					currentRealNodes = parentRealNode.getChildren(currentVirtualNodeID)
					if line[currentVirtualNodeID] in currentRealNodes:
						currentRealNode = currentRealNodes[currentRealNodes.index(line[currentVirtualNodeID])]
					else:
						currentRealNode = _RealNode(line[currentVirtualNodeID], currentVirtualNode.getJoiner(), currentVirtualNode.getChildNodeIDs(), currentVirtualNode)
						parentRealNode.addChild(currentRealNode, currentVirtualNodeID)
					queue.extend([(currentVirtualNode, child, currentRealNode) for child in currentVirtualNode.getChildren()])
			return True
		else:
			return False
	def mergeLines(self:object, lines:list, flags:list) -> int:
		if not isinstance(lines, (tuple, list)):
			return -1
		cnt = 0
		for line in lines:
			if self.mergeLine(line):
				 cnt += 1
		return cnt
	def summary(self:object) -> bytes:
		return bytes(self.__realRoot)
	def updateRoot(self:object, identifier:bytes) -> None:
		if isinstance(identifier, bytes):
			self.__realRoot = _RealNode(identifier, self.__virtualRoot.getJoiner(), self.__virtualRoot.getChildNodeIDs(), self.__virtualRoot)
			return True
		else:
			return False
	def __len__(self:object) -> int:
		return self.__length

class DynamicMergeMerge:
	def __init__(self:object, debugLevel:DebugLevel|int = 0) -> object:
		if isinstance(debugLevel, DebugLevel):
			self.__debugLevel = debugLevel
		else:
			try:
				self.__debugLevel = int(debugLevel)
			except:
				self.__debugLevel = 0
				self.__print("The debug level specified is invalid. It is defaulted to 0. ", Warning)
		self.__clear()
	def __clear(self:object) -> None:
		self.__flag = 0 # 0 = ready, 1 = initialized, 2 = executed
		self.__tree = Tree()
		self.__inputFilePaths = []
		self.__replacements = []
		self.__inputFilePointers = []
		self.__outputFilePath = None
		self.__outputColumns = None
		self.__outputFilePointer = None
	def __print(self:object, strings:str, dbgLevel:DebugLevel = Info, indentationCount:int = 0, indentationSymbol:str = "\t") -> bool:
		debugLevel = dbgLevel if isinstance(dbgLevel, DebugLevel) else Info
		if debugLevel >= self.__debugLevel:
			for string in strings.split("\n"):
				print("{0} {1}{2}".format(debugLevel, (str(indentationSymbol) * indentationCount if isinstance(indentationCount, int) and indentationCount >= 1 else ""), string))
			return True
		else:
			return False
	def __closeInputFilePointer(self:object, idx:int) -> bool:
		if isinstance(idx, int) and -len(self.__inputFilePointers) <= idx < len(self.__inputFilePointers):
			try:
				self.__inputFilePointers[idx].close()
				self.__print("Successfully close \"{0}\". ".format(self.__inputFilePaths[idx]), Debug)
				bRet = True
			except BaseException as e:
				self.__print("Failed to close \"{0}\". Details are as follows. \n{1}".format(self.__inputFilePaths[idx], e), Warning)
				bRet = False
			finally:
				self.__inputFilePointers[idx] = None
				return bRet
		else:
			self.__print("No files are closed since the passed index \"{0}\" is invalid. ".format(idx), Error)
			return False
	def __closeAllInputFilePointers(self:object) -> int:
		successCnt, totalCnt = 0, 0
		for idx, inputFilePointer in enumerate(self.__inputFilePointers):
			if inputFilePointer is None:
				totalCnt += 1
				if self.__closeInputFilePointer(idx):
					successCnt += 1
		self.__print("Successfully close {0} / {1} opened input file pointer(s). ".format(successCnt, totalCnt), Info)
	def __closeOutputFilePointer(self:object) -> bool:
		if self.__outputFilePointer is None:
			self.__print("The output file \"{0}\" has already been closed. No need to close it again. ".format(self.__outputFilePath), Debug)
			return True
		else:
			try:
				self.__outputFilePointer.close()
				self.__outputFilePointer = None
				self.__print("Successfully close \"{0}\". ".format(self.__outputFilePath), Info)
				return True
			except BaseException as e:
				self.__outputFilePointer = None
				self.__print("Failed to close \"{0}\". Details are as follows. \n{1}".format(self.__outputFilePath, e), Warning)
				return False
	def __handleFolder(self:object, fd:str) -> bool:
		folder = str(fd)
		if folder in ("", ".", "./", ".\\"):
			return True
		elif os.path.exists(folder):
			return os.path.isdir(folder)
		else:
			try:
				os.makedirs(folder)
				return True
			except:
				return False
	def __visualizeReplacements(self:object, width:int = 4, symbol:str = " ") -> str:
		# Preparation #
		w = width if isinstance(width, int) and width > 0 else 4
		s = symbol if isinstance(symbol, str) and len(symbol) == 1 and symbol not in ("\r", "\n") else " "
		treeLength = len(self.__tree)
		maxStringWidth = max([len(filePath) for filePath in self.__inputFilePaths] + [12])
		maxIntWidth = len(str(treeLength))
		for replacement in self.__replacements:
			for r in replacement:
				maxIntWidth = max(maxIntWidth, len(str(r[0])), len(str(r[1])))
		
		# Formatting #
		sRet = (symbol * width).join(["{{0:^{0}}}".format(maxStringWidth).format("Replacements")] + ["{{0:^{0}}}".format(maxIntWidth).format(i) for i in range(treeLength)])
		for idx, filePath in enumerate(self.__inputFilePaths):
			sRet += "\n{{0:^{0}}}".format(maxStringWidth).format(filePath)
			for i in range(treeLength):
				for sourceToken, targetToken in self.__replacements[idx]:
					if i == targetToken:
						sRet += symbol * width + "{{0:^{0}}}".format(maxIntWidth).format(sourceToken)
						break
				else:
					sRet += symbol * width + "{{0:^{0}}}".format(maxIntWidth).format("-")
		return sRet
	def initialize(								\
		self:object, config:dict, filePaths:tuple|list|set, replacements:tuple|list|set, 		\
		outputFilePath:str = "output.dynamicMergeMerge.tsv", 				\
		outputColumns:str|tuple|list|set = b"titleId\tprimaryTitle\ttitle (regions)\n"		\
	) -> bool:
		# Status Checking #
		if self.__flag > 0:
			self.__print("The merge-join object is already initialized. This will initialize the object again. ", Warning)
		self.__clear()
		
		# Preliminary Checking #
		if isinstance(config, Tree):
			self.__tree = deepcopy(config)
		elif isinstance(config, dict):
			cnt = self.__tree.build(config)
			if cnt:
				self.__print("Tree: \n{0}".format(self.__tree.getJson()), Debug)
				self.__print("Build {0} nodes on the tree. ".format(cnt), Info)
			else:
				self.__clear()
				self.__print("Failed to initialize the merge-join object since the tree is not constructed correctly. ", Error)
				return False
		else:
			self.__clear()
			self.__print("Failed to initialize the merge-join object since the tree is not passed correctly. ", Error)
			return False
		self.__inputFilePaths = list(filePaths) if isinstance(filePaths, (tuple, list, set)) else []
		self.__replacements = list(replacements) if isinstance(replacements, (tuple, list, set)) else []
		self.__outputFilePath = str(outputFilePath).strip()
		if isinstance(outputColumns, (tuple, list, set)):
			outputColumnsInBytes = []
			for outputColumn in outputColumns:
				if isinstance(outputColumn, bytes):
					outputColumnsInBytes.append(outputColumn)
			if len(outputColumnsInBytes) < len(outputColumns):
				self.__print("Not all the output columns passed are acceptable. The illegal ones have been skipped. ", Warning)
			self.__outputColumns = b"\t".join(outputColumnsInBytes) + b"\n"
		elif isinstance(outputColumns, bytes):
			self.__outputColumns = outputColumns
		else:
			self.__clear()
			self.__print("The passed output columns are not in acceptable formats. ", Error)
			return False
		
		# Further Checking #
		if not self.__inputFilePaths:
			self.__clear()
			self.__print("Failed to initialize the merge-join object since no files are passed. ", Error)
			return False
		elif not len(self.__inputFilePaths) == len(self.__replacements):
			self.__clear()
			self.__print("Failed to initialize the merge-join object since the lengths of the passed file paths and the replacements are not the same. ", Error)
			return False
		
		# Output Pointer Handling #
		if not self.__handleFolder(os.path.split(self.__outputFilePath)[0]):
			self.__clear()
			print("Failed to create \"{0}\" since the folder is not created successfully. ".format(self.__outputFilePath))
			return False
		try:
			self.__outputFilePointer = (gzipOpen if os.path.splitext(self.__outputFilePath)[1].lower() in (".gz", ) else open)(self.__outputFilePath, "wb")
			self.__outputFilePointer.write(self.__outputColumns)
			self.__outputFilePointer.flush()
		except BaseException as e:
			self.__clear()
			self.__print("Failed to open \"{0}\". Details are as follows. \n{1}".format(self.__outputFilePath, e), Error)
			return False
		
		# Initialization #
		self.__inputFilePointers = [None] * len(self.__inputFilePaths)
		for idx, filePath in enumerate(self.__inputFilePaths):
			# File Opening #
			try:
				self.__inputFilePointers[idx] = (gzipOpen if os.path.splitext(filePath)[1].lower() in (".gz", ) else open)(filePath, "rb")
			except BaseException as e:
				self.__inputFilePointers[idx] = None
				self.__print("Failed to open \"{0}\". Details are as follows. \n{1}".format(filePath, e), Error)
				continue
			
			# File Column Processing #
			columns = self.__inputFilePointers[idx].readline().split(b"\t")
			if len(set(columns)) != len(columns):
				self.__print("Repeated columns are found in \"{0}\". The file will be closed soon. ".format(filePath), Error)
				self.__closeInputFilePointer(idx)
				continue
			
			# Passed Replacement Index Handling #
			replacement = self.__replacements[idx]
			self.__replacements[idx] = []
			if isinstance(replacement, (tuple, list, set)):
				for r in replacement:
					if isinstance(r, (tuple, list)) and len(r) == 2:
						if isinstance(r[0], int) and isinstance(r[1], int) and -len(columns) <= r[0] < len(columns) and 0 <= r[1] < len(self.__tree):
							self.__replacements[idx].append((r[0], r[1]))
						elif isinstance(r[0], bytes) and isinstance(r[1], int) and r[0] in columns and 0 <= r[1] < len(self.__tree):
							self.__replacements[idx].append((columns.index(r[0]), r[1]))
						else:
							self.__print("An unrecognized replacement pair {0} is passed. This will be skipped. ".format(r), Warning)
					else:
						self.__print("An invalid replacement as follows is passed. This will be skipped. \n{0}".format(r), Warning)
				if not self.__replacements[idx]:
					self.__print("The replacement passed for \"{0}\" is empty. Since nothing should be read, the file will be closed soon. ".format(filePath), Warning)
					self.__closeInputFilePointer(idx)
			else:
				self.__print("The replacement passed for \"{0}\" is invalid. The file will be closed soon. ".format(filePath), Error)
				self.__closeInputFilePointer(idx)
		self.__print("Replacements: {0}\n{1}".format(self.__replacements, self.__visualizeReplacements()), Debug)
		
		# Status Updating #
		self.__flag = 1
		self.__print("Finish initializing with {0} / {1} input pointers and 1 output pointer opened. ".format(len(self.__inputFilePointers) - self.__inputFilePointers.count(None), len(self.__inputFilePointers)), Debug)
		return True
	def __readInputFile(self:object, idx:int) -> list:
		if isinstance(idx, int) and -len(self.__inputFilePointers) <= idx < len(self.__inputFilePointers) and self.__inputFilePointers[idx]:
			while True:
				# Pointer Checking #
				try:
					line = self.__inputFilePointers[idx].readline()
				except KeyboardInterrupt:
					raise KeyboardInterrupt
				except BaseException as e:
					self.__print("Failed to read a line from \"{0}\". Details are as follows. \n{1}\nThe file will be closed soon. ".format(self.__inputFilePaths[idx], e), Error)
					self.__closeInputFilePointer(idx)
					return None
				
				# EOF Checking #
				if not line:
					self.__print("Finish handling \"{0}\". The file will be closed soon. ".format(self.__inputFilePaths[idx]), Debug)
					self.__closeInputFilePointer(idx)
					return None
				
				# Line Checking #
				readItems, returnItems = line.strip().split(b"\t"), [None] * len(self.__tree)
				for r in self.__replacements[idx]:
					if -len(readItems) <= r[0] < len(readItems):
						returnItems[r[1]] = readItems[r[0]] # use the replacements to convert from the source column to the target column
					else:
						self.__print(																\
							"The index {0} is out of bound of the following line in \"{1}\". \n{2}This line has been skipped as the record is imcomplete and the next line will be read soon. ".format(	\
								r[0], self.__inputFilePaths[idx], line												\
							), Warning																\
						)
						break # read a new line if the inner loop is not ended naturally (continue reading the current file if the current line read is a failure or invalid)
				else: # The loop is ended naturally
					return returnItems
		else:
			self.__print("No files are closed since the passed index \"{0}\" is invalid or the file has already been closed. ".format(idx), Error)
			return None
	def merge(self:object) -> bool:
		# Status Checking #
		if self.__flag > 1:
			self.__flag = 1
			self.__print("The merge-join operation has already been done. This will process the merge-join operation again. ", Warning)
		elif self.__flag < 1:
			print("Please call ``initialize`` before calling ``merge``. ")
			return False
		
		# Preparation #
		length, lineCount, fp = len(self.__inputFilePointers), 0, self.__outputFilePointer
		lines = [None] * length
		
		# Main Algorithm #
		self.__print("Start to process the dynamic \"merge merge\" operation. Please use \"Ctrl + C\" to stop it if it is necessary. ", Info)
		startTime = time()
		for idx in range(length):
			lines[idx] = self.__readInputFile(idx)
		try:
			while any(self.__inputFilePointers):
				# Identifier Getting #
				identifier = min([line[0] for line in lines if line is not None])
				self.__tree.updateRoot(identifier)
				
				# Merging #
				for idx in range(length):
					while lines[idx] is not None and lines[idx][0] == identifier:
						self.__tree.mergeLine(lines[idx])
						lines[idx] = self.__readInputFile(idx)
				
				# Next #
				results = self.__tree.summary()
				try:
					fp.write(results)
					fp.flush()
					lineCount += 1
					if not lineCount % 5000000:
						timeDelta = time() - startTime
						self.__print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(lineCount, self.__outputFilePath, timeDelta, lineCount / timeDelta), Info)
					elif not lineCount % 1000000:
						timeDelta = time() - startTime
						self.__print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(lineCount, self.__outputFilePath, timeDelta, lineCount / timeDelta), Debug)
				except KeyboardInterrupt:
					raise KeyboardInterrupt
				except BaseException as e:
					self.__print("Failed to write the following byte strings to \"{0}\". \n{1}\nDetails are as follows. \n{2}".format(self.__outputFilePath, results, e), Warning)
		except KeyboardInterrupt:
			timeDelta = time() - startTime
			self.__closeOutputFilePointer()
			self.__closeAllInputFilePointers()
			self.__print("The dynamic \"merge merge\" operation is interrupted by users. ", Warning)
			self.__print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(lineCount, self.__outputFilePath, timeDelta, lineCount / timeDelta), Info)
			self.__flag = 1
			return False
		except BaseException as e:
			timeDelta = time() - startTime
			self.__closeOutputFilePointer()
			self.__closeAllInputFilePointers()
			self.__print("Exceptions occurred during the main algorithm. Details are as follows. \n{0}".format(e), Error)
			self.__print("Successfully process {0} data in {1:.3f} second(s) at {2:.3f} datum/s. ".format(lineCount, timeDelta, lineCount / timeDelta), Info)
			self.__flag = 1
			return False
		else:
			timeDelta = time() - startTime
			self.__print("Successfully write {0} datum lines to \"{1}\" in {2:.3f} second(s) at {3:.3f} datum/s. ".format(lineCount, self.__outputFilePath, timeDelta, lineCount / timeDelta), Info)
			if self.__closeOutputFilePointer():
				self.__flag = 2
				return True
			else:
				self.__flag = 1
				return False


def preExit(countdownTime:int = 5) -> None:
	try:
		cntTime = int(countdownTime)
		length = len(str(cntTime))
	except:
		print("Program ended. ")
		return
	print()
	while cntTime > 0:
		print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(cntTime), end = "")
		try:
			sleep(1)
		except:
			print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(0))
			return
		cntTime -= 1
	print("\rProgram ended, exiting in {{0:>{0}}} second(s). ".format(length).format(cntTime))

def main() -> int:
	dynamicMergeMerge = DynamicMergeMerge()
	if not dynamicMergeMerge.initialize(													\
		# {"formatter":b"{0}\t{1}\t{2}\n", "joiner":b"\t", "children":[{}, {"formatter":b"{0} ({1})", "joiner":b",", "children":[{}]}]}, 				\
		{"formatter":b"%b\t%b\t%b\n", "joiner":b"\t", "children":[{"formatter":b"%b"}, {"formatter":b"%b (%b)", "joiner":b",", "children":[{"formatter":b"%b"}]}]}, 	\
		["title.basics.tsv", "title.akas.tsv"], [[(b"tconst", 0), (b"primaryTitle", 1)], [(b"titleId", 0), (b"title", 2), (b"region", 3)]]					\
	):
		print("Please make sure the files are readable and the columns exist. ")
		preExit()
		return EOF
	bRet = dynamicMergeMerge.merge()
	preExit()
	return EXIT_SUCCESS if bRet else EXIT_FAILURE



if __name__ == "__main__":
	exit(main())