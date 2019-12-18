
MAX_STACK_SIZE = 65536

class Stack:
    def __init__(self):
        self.data = []
        self.size = 0
    
    def pop(self):
        if self.size == 0:
            print("Stack underflow!")
            exit(1)
        self.size -= 1
        return self.data.pop()
    
    def push(self, value):
        if self.size >= MAX_STACK_SIZE:
            print("Stack overflow!")
            exit(1)
        self.data.append(value)
        self.size += 1

class VM:
    def __init__(self, code):
        self.data = Stack()
        self.code = Stack()
        self.output = Stack()
        self.functions = [Stack()]*20
        
        for i in code:
            self.code.push(i)
        
    def execute(self):
        while self.code.size > 0:
            self.execute_one_inst()
    

    def execute_one_inst(self):

        inst = self.code.pop()
        
        # Push inst on data
        if inst < 0x80:
            self.data.push(inst)
            return
        
        # XOR data with 0x80
        if inst == 0x80:
            self.data.push(self.data.pop() ^ 0x80)
            return
        
        # Make top of stack 0xff if it's 0, else 0x00
        if inst == 0x81:
            val = self.data.pop()
            if val == 0:
                self.data.push(0xff)
            else:
                self.data.push(0)
            return
        
        # a AND b
        if inst == 0x82:
            a = self.data.pop()
            b = self.data.pop()
            self.data.push(a & b)
            return
        
        # a OR b
        if inst == 0x83:
            a = self.data.pop()
            b = self.data.pop()
            self.data.push(a | b)
            return
        
        # a XOR b
        if inst == 0x84:
            a = self.data.pop()
            b = self.data.pop()
            self.data.push(a ^ b)
            return
        
        # Swap a and b on stack
        if inst == 0x90:
            a = self.data.pop()
            b = self.data.pop()
            self.data.push(a)
            self.data.push(b)
            return
        
        # Duplicate top of stack
        if inst == 0x91:
            val = self.data.pop()
            self.data.push(val)
            self.data.push(val)
            return
        
        # Move data into functions[index]
        if inst == 0xa0:
            index = self.data.pop()
            if index >= 0x20:
                print("Invalid index")
                exit(1)
            self.functions[index].size = 0
            
            c = self.data.pop()
            while c != 0xa1:
                self.functions[index].push(c)
                c = self.data.pop()
            return
        
        # Move data into output
        if inst == 0xb0:
            self.output.push(self.data.pop())
            return
        
        # Move func instructions to data
        if inst >= 0xc0 and inst < 0xe0:
            index = inst - 0xc0
            func = self.functions[index]
            for i in range(func.size, 0, -1):
                self.code.push(func.data[i-1])
            return
        
        # Move func instructions to data if top of data stack > 0
        if inst >= 0xe0:
            index = inst - 0xe0
            if self.data.pop() > 0:
                func = self.functions[index]
                for i in range(func.size, 0, -1):
                    self.code.push(func.data[i-1])
            return

if __name__ == '__main__':

    # Get length of the code
    length = int(input("Length: "))
    if length <= 0 or length >= 65535:
        print("Invalid length")
        exit(1)
    
    # Get the code to run (as a list of ints)
    code_input = input("Code: ")
    user_code = [int(x) for x in bytes.fromhex(code_input)[:length]]
    
    vm = VM(user_code)
    vm.execute()
    
    # Check results from execution
    if length != vm.output.size or vm.output.data != user_code:
        print("No")
        [print(hex(x)) for x in vm.output.data]
        exit(1)
    else:
        print("YES")
    