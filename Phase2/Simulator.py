class ISB:
    def __init__(self,pc=0):
        self.operation=-1
        self.opcode=-1
        self.rs1=-1
        self.rs2=-1
        self.rd=-1
        self.imm=-1
        self.PC=pc
        self.PC_temp=0
        self.IR=0
        self.RA=0
        self.RB=0
        self.MDR=0
        self.Alu_out=-1
        self.is_actual_instruction=False
        self.branchRA=-1
        self.branchRB=-1

class ControlUnit:

    def __init__(self,file_name):
        self.MEM={}
        self.MachineCode=[]
        self.RegisterFile=[0 for i in range(32)]
        self.RegisterFile[2]=int('0x7FFFFFF0',16)
        self.RegisterFile[3]=int('0x10000000',16)
        self.cycles=0
        self.count_mem_ins=0
        self.count_ins=0
        self.count_control_ins=0
        self.count_alu_inst=0
        self.stalls=0
        self.branch_mispred=0
        self._program_memory(file_name)

    def _program_memory(self,file_name):
        File=open(file_name)
        while True:
            inst=File.readline()
            try:
                _,inst=inst.split()
                inst=int(inst,16)
                self.MachineCode.append(inst)
            except ValueError:
                break
        while True:
            inst=File.readline()
            if inst:
                key,val=inst.split()
                self.MEM[int(key,16)]=int(val,16)
            else:
                break
        File.close()

    def twoscomplement(self,decimal_number,length):
        binary=bin(decimal_number).replace('0b','')
        binary='0'*(length-len(binary))+binary
        if binary[0]=='0':
            return decimal_number
        return decimal_number-(2**length)

    def store_State(self,file_name='Store.txt'):
        file=open(file_name,'w')
        file.write('Registers\n')
        file.write('-'*20)
        file.write('\n')
        for i in range(32):
            file.write(str(self.RegisterFile[i]))
            file.write('\n')
        file.write('-'*20)
        file.write('\n')
        file.write('Memory')
        file.write('\n')
        file.write('-'*20)
        file.write('\n')
        file.write("Memory : Value")
        file.write('\n')
        for key in self.MEM.keys():
            file.write(str(key)+" : "+str(self.MEM[key]))
            file.write('\n')

    def fetch(self,state,btb):
        try:
            state.IR=self.MachineCode[state.PC//4]
            state.PC_temp=state.PC+4
            state.is_actual_instruction=True
            opcode=state.IR &(0x7F)
            state.opcode=opcode
            if opcode==99:
                rs1=state.IR&(0xF8000)
                rs1=rs1>>15
                state.rs1=rs1
                rs2=state.IR&(0x1F00000)
                rs2=rs2>>20
                state.rs2=rs2
                func3=state.IR&(0x7000)
                func3=func3>>12
                temp=bin(state.IR).replace('0b','')
                temp='0'*(32-len(temp))+temp
                immediate=temp[0]+temp[-8]+temp[1:7]+temp[20:24]+'0'
                state.imm=int(immediate,2)
                if func3==0:
                    state.operation='beq'
                elif func3==1:
                    state.operation='bne'
                elif func3==5:
                    state.operation='bge'
                elif func3==4:
                    state.operation='blt'
            elif opcode==103:
                rs1=state.IR&(0xF8000)
                rs1=rs1>>15
                state.rs1=rs1
                imm=state.IR&(0xFFF00000)
                imm=imm>>20
                state.imm=imm
                rd=state.IR&(0xF80)
                rd=rd>>7
                state.rd=rd
                func3=state.IR&(0x7000)
                func3=func3>>12
                state.RA=self.RegisterFile[rs1] 
                state.operation='jalr'                         
            if btb==0:
                return state
            new_pc=0
            outcome=False
            if btb.targetBTB(state.PC)!=-1:
                new_pc=btb.targetBTB(state.PC)
                outcome=True
            return  outcome,new_pc,state
        except IndexError:
            state.IR=0
            state.is_actual_instruction=False
            if btb==0:
                return state
            return False,0,state

    def decode(self,state,btb):
        control_hazard=False
        new_pc=0
        state.Alu_out=-1
        if state.is_actual_instruction==False:
            return control_hazard, new_pc, state
        opcode=state.IR & (0x7F)
        state.opcode=opcode
        #R type instructions
        if opcode==51:
            self.count_alu_inst+=1
            rs1=state.IR&(0xF8000)
            rs1=rs1>>15
            state.rs1=rs1
            rs2=state.IR&(0x1F00000)
            rs2=rs2>>20
            state.rs2=rs2
            rd=state.IR&(0xF80)
            rd=rd>>7
            state.rd=rd
            func7=state.IR&(0xFE000000)
