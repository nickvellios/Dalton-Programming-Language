"""
Dalton Programmming Language
Created by Nick Vellios
8/2018

I was freshening up on Python and playing around with string manipulation.
I was testing the performance of manually parsing strings vs using regular
expressions and my curiousity grew and I began building out an interpreter
for this made up language.  Nothing was planned ahead, and the code mostly
reflects that.  It's very hacked together.  But hell, it works.  :)

License:  None.  Do whatever you want with it.
"""

variables = {}
jumpStack = {}

class ForState:
	def __init__(self):
		self.startPos = None
		self.variable = None
		self.to = None

forStates = []

class Stack:
	def __init__(self, c):
		self.pos = 0
		self.jumpReturnOffset = None
		self.code = c

	def char(self):
		if self.pos < len(self.code):
			return self.code[self.pos]
		else:
			return "\n"

	def program(self):
		return self.code

	def length(self):
		return len(self.code)

	def step(self, distance):
		if self.pos + distance > len(self.code):
			raise Exception("Out of bounds step operation")
		self.pos += distance

	def back(self, distance):
		if self.pos == 0:
			raise Exception("Out of bounds step operation")

		self.pos -= distance

	def peek(self):
		if self.pos + 1 < len(self.code):
			return self.code[self.pos + 1]
		else:
			return " " # EOF

	def jump(self, p):
		if p > len(self.code):
			raise Exception("Out of bounds jump operation")

		self.pos = p

	def position(self):
		return self.pos

	def advanceWhitespace(self):
		while self.pos+1 < len(self.code) and (self.char() == " " or self.char() == "\t"):
			self.step(1)
	
	def advanceToNextline(self):
		string = ''
		while self.pos < len(self.code) and self.char() != "\n":
			string += self.char()
			self.step(1)

		if self.pos < len(self.code):
			self.step(1)
		return string

	def consumeString(self):
		string = ''
		self.step(1)
		while self.char() != '"':
			string += self.char()
			self.step(1)
		self.step(1)

		return string
	
	def consumeDigit(self):
		digits = ''
		if self.char() == "-" and self.peek().isdigit():
			digits = "-"
			self.step(1)

		while self.char().isdigit() or self.char() == ".":
			digits += self.char()
			self.step(1)

		return digits

	def consumeVariable(self):
		variable = ''
		while self.char().isalnum():
			variable += self.char()
			self.step(1)

		if variable not in variables:
			variables[variable] = None
		return variable
		
	def jumpReturn(self):
		if self.jumpReturnOffset != None:
			self.jump(self.jumpReturnOffset)

		self.jumpReturnOffset = None

	def storeReturnOffset(self):
		self.jumpReturnOffset = self.pos

def enum(**enums):
    return type('Enum', (), enums)

tokens = enum(
	TOK_ERROR = 1,
	TOK_CR = 2,
	TOK_NUMBER = 3,
	TOK_STRING = 4,
	TOK_VARIABLE = 5,
	TOK_LET = 6,
	TOK_PRINT = 7,
	TOK_IF = 8,
	TOK_FOR = 11,
	TOK_TO = 12,
	TOK_GOTO = 14,
	TOK_CALL = 15,
	TOK_RETURN = 16,
	TOK_XOR = 17,
	TOK_END = 18,
	TOK_PLUS = 19,
	TOK_MINUS = 20,
	TOK_AND = 21,
	TOK_OR = 22,
	TOK_ASTR = 23,
	TOK_SLASH = 24,
	TOK_MOD = 25,
	TOK_GTLT = 28,
	TOK_NOTEQ = 29,
	TOK_LT = 30,
	TOK_GT = 31,
	TOK_EQ = 32,
	TOK_ENDFUNCTION = 33,
	TOK_EIF = 34,
	TOK_BREAK = 35,
	TOK_INPUT = 36,
	TOK_COMMENT = 37,
)

tokenStr = {
	tokens.TOK_ERROR: "error",
	tokens.TOK_CR: "\n",
	tokens.TOK_NUMBER: "number",
	tokens.TOK_STRING: "string",
	tokens.TOK_VARIABLE: "variable",
	tokens.TOK_LET: "let",
	tokens.TOK_PRINT: "print",
	tokens.TOK_IF: "if",
	tokens.TOK_FOR: "for",
	tokens.TOK_TO: "to",
	tokens.TOK_GOTO: "goto",
	tokens.TOK_CALL: "call",
	tokens.TOK_RETURN: "return",
	tokens.TOK_BREAK: "break",
	tokens.TOK_INPUT: "input",
	tokens.TOK_XOR: "^",
	tokens.TOK_EIF: "eif",
	tokens.TOK_END: "end",
	tokens.TOK_PLUS: "+",
	tokens.TOK_MINUS: "-",
	tokens.TOK_AND: "&",
	tokens.TOK_OR: "|",
	tokens.TOK_ASTR: "*",
	tokens.TOK_SLASH: "/",
	tokens.TOK_MOD: "%",
	tokens.TOK_GTLT: "<>",
	tokens.TOK_NOTEQ: "!=",
	tokens.TOK_LT: "<",
	tokens.TOK_GT: ">",
	tokens.TOK_EQ: "=",
	tokens.TOK_ENDFUNCTION: "@end",
	tokens.TOK_COMMENT: "#",
}

keywords = {
	"let": tokens.TOK_LET,
	"print": tokens.TOK_PRINT,
	"if": tokens.TOK_IF,
	"for": tokens.TOK_FOR,
	"to": tokens.TOK_TO,
	"goto": tokens.TOK_GOTO,
	"call": tokens.TOK_CALL,
	"return": tokens.TOK_RETURN,
	"break": tokens.TOK_BREAK,
	"input": tokens.TOK_INPUT,
	"eif": tokens.TOK_EIF,
	"end": tokens.TOK_END,
	"@end": tokens.TOK_ENDFUNCTION,
	"<>": tokens.TOK_GTLT,
	"!=": tokens.TOK_NOTEQ,
}

stack = None

def get_next_token():
	global stack

	stack.advanceWhitespace()
	pos = stack.position()
	# Search for known keywords
	for keyword, keyID in keywords.iteritems():
		if pos+len(keyword) <= stack.length():
			if keyword == stack.code[pos:(pos+len(keyword))] and (stack.code[pos + len(keyword)] == ' ' or stack.code[pos + len(keyword)] == "\n"):
				return keywords[keyword]

	# Check if number
	if stack.char().isdigit():
		return tokens.TOK_NUMBER

	# Check if variable
	if stack.char().isalpha():
		return tokens.TOK_VARIABLE

	# Check if function location skip to the end.
	if stack.char() == '@':
		stack.advanceToNextline()
		tok = get_next_token()

		while tok != tokens.TOK_ENDFUNCTION:
		 	stack.advanceToNextline()
			tok = get_next_token()
		
		return tokens.TOK_CR

	# Check if string
	if stack.char() == '"':
		return tokens.TOK_STRING
	
	# Check if newline
	if stack.char() == "\n":
		return tokens.TOK_CR

	# Check if operand
	if stack.char() == '+':
		return tokens.TOK_PLUS

	if stack.char() == '-':
		if stack.peek().isdigit():
			return tokens.TOK_NUMBER
		else:
			return tokens.TOK_MINUS

	if stack.char() == '*':
		return tokens.TOK_ASTR

	if stack.char() == '/':
		return tokens.TOK_SLASH

	if stack.char() == '&':
		return tokens.TOK_AND

	if stack.char() == '|':
		return tokens.TOK_OR

	if stack.char() == '^':
		return tokens.TOK_XOR

	if stack.char() == '%':
		return tokens.TOK_MOD

	if stack.char() == '<':
		return tokens.TOK_LT

	if stack.char() == '>':
		return tokens.TOK_GT

	if stack.char() == '=':
		return tokens.TOK_EQ

	if stack.char() == '#':
		stack.advanceToNextline()

		return tokens.TOK_COMMENT

	return None

def stepAdvanceGetToken(tok):
	global stack
	stack.step(len(tokenStr[tok]))
	stack.advanceWhitespace()

	return get_next_token()

def expression():
	global stack

	tok = get_next_token()
	if tok == tokens.TOK_NUMBER:
		term = float(stack.consumeDigit())

	if tok == tokens.TOK_VARIABLE:
		variable = str(variables[stack.consumeVariable()])
		
		if variable.replace('.', '', 1).isdigit():
			term = float(variable)
		else:
			term = variable

	if tok == tokens.TOK_STRING:
		term = stack.consumeString()

	tok = get_next_token()

	while tok != tokens.TOK_CR and tok != tokens.TOK_TO and tok != tokens.TOK_NOTEQ \
			and tok != tokens.TOK_EQ and tok != tokens.TOK_GTLT and tok != tokens.TOK_GT and tok != tokens.TOK_LT:
		if tok == tokens.TOK_PLUS:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				dig = stack.consumeDigit()

				if str(dig).replace('.', '', 1).isdigit() and str(term).replace('.', '', 1).isdigit():
					term = float(term) + float(dig)
				else:
					term = str(term) + str(dig)

			if tok == tokens.TOK_VARIABLE:
				var = stack.consumeVariable()
				term2 = variables[var]

				if str(term2).replace('.', '', 1).isdigit() and str(term).replace('.', '', 1).isdigit():
					term = float(term) + float(term2)
				else:
					term = str(term) + str(term2)

			if tok == tokens.TOK_STRING:
				term = term + stack.consumeString()

		elif tok == tokens.TOK_NUMBER:
			dig = stack.consumeDigit()
			
			if len(dig):
				term = term + float(dig)

			tok = get_next_token()

		elif tok == tokens.TOK_MINUS:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				term = term - float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = term - float(variables[stack.consumeVariable()])

		elif tok == tokens.TOK_ASTR:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				term = term * float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = term * float(variables[stack.consumeVariable()])
		
		elif tok == tokens.TOK_SLASH:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				term = term / float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = term / float(variables[stack.consumeVariable()])

		elif tok == tokens.TOK_AND:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				term = term & int(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = term & int(variables[stack.consumeVariable()])

		elif tok == tokens.TOK_OR:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				term = int(term) | int(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = int(term) | int(variables[stack.consumeVariable()])

		elif tok == tokens.TOK_MOD:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				term = int(term) % int(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = int(term) % int(variables[stack.consumeVariable()])

		elif tok == tokens.TOK_XOR:
			tok = stepAdvanceGetToken(tok)

			if tok == tokens.TOK_NUMBER:
				term = int(term) ^ int(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = int(term) ^ int(variables[stack.consumeVariable()])

		else:
			tok = get_next_token()
		

	term = str(term)

	if term.replace('.', '', 1).isdigit():
		if float(term) == 0:
			return str("0")
		return term.rstrip('0').rstrip('.')

	return term

def condition():
	global stack

	tok = get_next_token()
	term = expression()
	tok = get_next_token()

	while tok != tokens.TOK_CR:
		if tok == tokens.TOK_GTLT:
			tok = stepAdvanceGetToken(tok)
			if tok == tokens.TOK_NUMBER:
				term = float(term) <> float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = float(term) <> float(variables[stack.consumeVariable()])

			if tok == tokens.TOK_STRING:
				term = str(term) <> str(stack.consumeString())
		elif tok == tokens.TOK_NOTEQ:
			tok = stepAdvanceGetToken(tok)
			if tok == tokens.TOK_NUMBER:
				term = float(term) != float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = float(term) != float(variables[stack.consumeVariable()])

			if tok == tokens.TOK_STRING:
				term = str(term) != str(stack.consumeString())

		elif tok == tokens.TOK_GT:
			tok = stepAdvanceGetToken(tok)
			if tok == tokens.TOK_NUMBER:
				term = float(term) > float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = float(term) > float(variables[stack.consumeVariable()])

		elif tok == tokens.TOK_LT:
			tok = stepAdvanceGetToken(tok)
			if tok == tokens.TOK_NUMBER:
				term = float(term) < float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = float(term) < float(variables[stack.consumeVariable()])

		elif tok == tokens.TOK_EQ:
			tok = stepAdvanceGetToken(tok)
			if tok == tokens.TOK_NUMBER:
				term = float(term) == float(stack.consumeDigit())

			if tok == tokens.TOK_VARIABLE:
				term = float(term) == float(variables[stack.consumeVariable()])

			if tok == tokens.TOK_STRING:
				term = str(term) == str(stack.consumeString())
		else:
			tok = get_next_token()
		
	return True if term else False

def execute(code):
	global stack
	global jumpStack
	stack = Stack(code + "\n")

	# Build jump table
	while stack.position() < stack.length():
		char = stack.char()

		if char == '@' and stack.peek() != 'e' and code[stack.position() + 2] != 'n' and code[stack.position() + 3] != 'd':
			stack.step(1)
			functionEnd = stack.advanceToNextline()
			jumpStack[functionEnd] = stack.position()

			continue

		stack.step(1)

	stack.jump(0)

	while stack.position() < stack.length():
		tok = get_next_token()

		if tok:
			if tok == tokens.TOK_IF:
				stack.step(len(tokenStr[tok]))
				tok = get_next_token()
				if not condition():
					ifcount = 1
					while ifcount > 0:
						stack.advanceToNextline()
						tok = get_next_token()
						if tok == tokens.TOK_IF:
							ifcount += 1
						
						if tok == tokens.TOK_EIF:
							ifcount -= 1

			elif tok == tokens.TOK_FOR:
				tok = stepAdvanceGetToken(tok)
				newForState = ForState()
				variable = stack.consumeVariable()
				tok = get_next_token()
				tok = stepAdvanceGetToken(tok) 
				newForState.variable = variable
				variables[variable] = expression()
				tok = get_next_token()
				tok = stepAdvanceGetToken(tok) # to value
				newForState.to = expression()
				stack.advanceWhitespace()
				newForState.startPos = stack.pos
				forStates.append(newForState)

			elif tok == tokens.TOK_END:
				forState = forStates[-1]
				variables[forState.variable] = str(int(variables[forState.variable]) + 1)
				if int(variables[forState.variable]) > int(forState.to):
					tok = get_next_token()
					del forStates[-1]
				else:
					stack.jump(forState.startPos)

			elif tok == tokens.TOK_BREAK:
				del forStates[-1]
				forcount = 1

				while forcount > 0:
					stack.advanceToNextline()
					tok = get_next_token()
					if tok == tokens.TOK_FOR:
						forcount += 1
					
					if tok == tokens.TOK_END:
						forcount -= 1

			elif tok == tokens.TOK_RETURN:
				if stack.jumpReturnOffset:
					stack.jumpReturn()
					tok = get_next_token()
				else:
					while tok != tokens.TOK_ENDFUNCTION:
						stack.advanceToNextline()
						tok = get_next_token()

			elif tok == tokens.TOK_CALL:
				stack.step(len(tokenStr[tok]))
				stack.advanceWhitespace()
				jumpLocation = stack.advanceToNextline()
				stack.storeReturnOffset()
				stack.jump(jumpStack[jumpLocation] - len(jumpLocation))
				tok = get_next_token()

			elif tok == tokens.TOK_GOTO:
				stack.step(len(tokenStr[tok]))
				stack.advanceWhitespace()
				jumpLocation = stack.advanceToNextline()
				stack.jump(jumpStack[jumpLocation] - len(jumpLocation))
				tok = get_next_token()

			elif tok == tokens.TOK_ENDFUNCTION:
				stack.jumpReturn()
				tok = get_next_token()

			elif tok == tokens.TOK_PRINT:
				stack.step(len(tokenStr[tok]))
				tok = get_next_token()

				if tok == tokens.TOK_NUMBER or tok == tokens.TOK_VARIABLE or tok == tokens.TOK_STRING:
					print expression()

			elif tok == tokens.TOK_INPUT:
				stack.step(len(tokenStr[tok]))
				tok = get_next_token()

				if tok == tokens.TOK_VARIABLE:
					variable = stack.consumeVariable()
					variables[variable] = raw_input(">>> ")

			elif tok == tokens.TOK_LET:
				stack.step(len(tokenStr[tok]))
				tok = get_next_token()

				if tok == tokens.TOK_VARIABLE:
					variable = stack.consumeVariable()
					tok = get_next_token()

					if tok == tokens.TOK_EQ:
						stack.step(len(tokenStr[tok]))
						tok = get_next_token()

						if tok == tokens.TOK_NUMBER or tok == tokens.TOK_VARIABLE or tok == tokens.TOK_STRING:
							variables[variable] = expression()

		stack.advanceToNextline()

with open('example.dal', 'r') as source:
  execute(source.read())