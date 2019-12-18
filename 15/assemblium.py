
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
            print(f"{hex(inst)}: {hex(inst)} -> [data]")
            self.data.push(inst)
            return
        
        # XOR data with 0x80
        if inst == 0x80:
            val = self.data.pop()
            print(f"{hex(inst)}: [data] {hex(val)} ^ 0x80 ({hex(val^0x80)}) -> [data]")
            self.data.push(self.data.pop() ^ 0x80)
            return
        
        # Make top of stack 0xff if it's 0, else 0x00
        if inst == 0x81:
            val = self.data.pop()
            if val == 0:
                print(f"{hex(inst)}: val={hex(val)} | Push 0xff -> [data]")
                self.data.push(0xff)
            else:
                print(f"{hex(inst)}: val={hex(val)} | Push 0x0 -> [data]")
                self.data.push(0)
            return
        
        # a AND b
        if inst == 0x82:
            a = self.data.pop()
            b = self.data.pop()
            print(f"{hex(inst)}: [data] {hex(a)} & {hex(b)} = {hex(a&b)} -> [data]")
            self.data.push(a & b)
            return
        
        # a OR b
        if inst == 0x83:
            a = self.data.pop()
            b = self.data.pop()
            print(f"{hex(inst)}: [data] {hex(a)} | {hex(b)} = {hex(a|b)} -> [data]")
            self.data.push(a | b)
            return
        
        # a XOR b
        if inst == 0x84:
            a = self.data.pop()
            b = self.data.pop()
            print(f"{hex(inst)}: [data] {hex(a)} ^ {hex(b)} = {hex(a^b)} -> [data]")
            self.data.push(a ^ b)
            return
        
        # Swap a and b on stack
        if inst == 0x90:
            a = self.data.pop()
            b = self.data.pop()
            print(f"{hex(inst)}: [data] ({hex(a)},{hex(b)}) >> ({hex(b)},{hex(a)} -> [data]")
            self.data.push(a)
            self.data.push(b)
            return
        
        # Duplicate top of stack
        if inst == 0x91:
            val = self.data.pop()
            print(f"{hex(inst)}: [data] {hex(val)} x2 -> [data]")
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
            print(f"{hex(inst)}: From [data] -> [func[{index}]]...")
            while c != 0xa1:
                print(f"    {hex(c)}")
                self.functions[index].push(c)
                c = self.data.pop()
            return
        
        # Move data into output
        if inst == 0xb0:
            val = self.data.pop()
            print(f"{hex(inst)}: [data] {hex(val)} -> [ouput]")
            self.output.push(self.data.pop())
            return
        
        # Move func instructions to data
        if inst >= 0xc0 and inst < 0xe0:
            index = inst - 0xc0
            func = self.functions[index]
            print(f"{hex(inst)}: From [func[{index}] -> [code]...")
            for i in range(func.size, 0, -1):
                val = func.data[i-1]
                print(f"    {hex(val)}")
                self.code.push(val)
            return
        
        # Move func instructions to data if top of data stack > 0
        if inst >= 0xe0:
            index = inst - 0xe0
            chk = self.data.pop()
            if chk > 0:
                print(f"{hex(inst)}: From [func[{index}] -> [code]...")
                print(f"{chk} > 0")
                func = self.functions[index]
                for i in range(func.size, 0, -1):
                    val = func.data[i-1]
                    print(f"    {hex(val)}")
                    self.code.push(val)
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
        print("\nOUTPUT")
        print(' '.join(["{:02x}".format(i) for i in vm.output.data]))
        print("\nCODE")
        print(' '.join(["{:02x}".format(i) for i in user_code]))
        print("\nDATA")
        print(' '.join(["{:02x}".format(i) for i in vm.data.data]))
        exit(1)
    else:
        print("YES")
    
