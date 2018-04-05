

class KB():

    flist = []
    elist = []
    guests = []
    tables = []
    oriClause = []

    def __init__(self,li,gt):
        for i in range(int(gt[0])):
            self.guests.append(i+1)
        for i in range(int(gt[1])):
            
            self.tables.append(i+1)
        for i in range(len(li)):
            if li[i][2] =='F':
                self.flist.append(li[i])
        for i in range(len(li)):
            if li[i][2] =='E':
                self.elist.append(li[i])
    
    def makeCNF(self): #use list to represent each clause
        c = []

        #one guest cannot sit at two tables:
        for i in range(len(self.guests)):
            
            
            for j in range(len(self.tables)):   
            
                if j != len(self.tables)-1:
                    for k in range(j+1,len(self.tables)):
                        
                        a = ['~', str(i+1),str(j+1)]
                        b = ['~',str(i+1),str(k+1)]
                        
                        self.oriClause.append([a,b])
        for i in range(len(self.guests)):
            
            d = []
            for j in range(len(self.tables)):   
                s = [str(i+1) , str(j+1)]
            
                d.append(s)
            self.oriClause.append(d)


        #for friends seating
        for i in range(len(self.flist)):
            for j in range(len(self.tables)):

                a = ['~', str(self.flist[i][0]),str(j+1) ]
                b=[ str(self.flist[i][1]),str(j+1)]
                d = [a,b]
                x = [str(self.flist[i][0]),str(j+1)]
                y =['~' ,str(self.flist[i][1]),str(j+1)]
                e = [x,y]
                
                self.oriClause.append(d)
                self.oriClause.append(e)

        #for enemy seating
        for i in range(len(self.elist)):
            for j in range(len(self.tables)):
                
                s = ['~', str(self.elist[i][0]),str(j+1)]
                t = ['~', str(self.elist[i][1]),str(j+1)]
                d = [s,t]
                self.oriClause.append(d)

        return self.oriClause


    def standardOutput(self,model):
        assign = {}
        mn = {}
        for i in model:
            if len(i) == 2:
                assign[i[0]] = i[1]

            else:
                
                if i[1] not in assign:

                    mn.setdefault(i[1],self.tables)

        for x in mn:
            for p in model:
                if len(p) == 3:
                    if p[1] == x:
                        if int(p[2])in mn[x]:
                            mn[x].remove(int(p[2]))
        if len(assign) ==len(self.guests):

            return assign
        else:
            return False
        for x in mn:
            if len(mn[x]) == 0:

                return False
            else:
                assign[x]= mn[x][0]

    


def allT(cls,model):
    
    for c in cls:
        v = [li for li in c if li in model]
        if len(v) == 0:
        
            return False
    
    return True


def someF(cls,model):
    mc = compliment(model)

    for c in cls:
        v = [li for li in c if li not in mc]
        if len(v)==0:
            return True
    
    return False 



def dpll(cls,model): # 3 rules
    if allT(cls,model):
        return model
    if someF(cls,model):
        return False
    
    p= pureClause(cls,model)
    if p:
        return dpll(cls,model+[p])

    u = unitClause(cls,model)
    if u:
        return dpll(cls,model+[u])

    s = splitClause(cls,model)
        
    if s:
        r= dpll(cls,model+[s])
        if r:
            return r
        else:
    
            r = dpll(cls,model+[['~',s[0],s[1]]])
                
            if r:
                return r
            else:
                return False

    

def splitClause(cls,model):
    cm = model + compliment(model)
    
    for c in cls:
        for a in c:
            if len(a) == 2 and a not in cm:
                return a
    return False
    



def unitClause(cls,model):#only one literal in a clause
    mc = compliment(model)
    for c in cls:
        r = [var for var in c if var not in mc]
        if len(r) == 1:
            if r[0] not in model:
                
                return r[0]
    return False


def pureClause(cls,model):#only one symbol appear in all clause, such as ~P
    mc = compliment(model)
    can = []
    for c in cls:
        v = [li for li in c if li in model]
        if len(v) == 0:
            can = can + [li for li in c]
    cc = compliment(can)
    pure = [li for li in can if li not in cc]
    for li in pure:
        if li not in model and li not in mc:
            
            return li
    return False




def compliment(lit):
    result = []
    for l in lit:
        if l[0] == '~':
            result.append([l[1],l[2]])
        else:
            result.append(['~',l[0],l[1]])
    return result


def main():
    f1 = open('input.txt','r')
    s = f1.readlines()
    info = s[0].strip().split()
    relations = []
    #print info
    for i in range(1,len(s)):
        relations.append(s[i].strip().split())
    sol = KB(relations,info)

    a = sol.makeCNF()

    #print a
    finalmodel = dpll(a,[])


    #print finalmodel

    f2 = open('output.txt','w')
    if finalmodel != False:
        op = sol.standardOutput(finalmodel)
        #print op
        if op != False:

            x  = sorted(op)
            if len(x)>0:
                f2.write(''+ 'yes' + '\n')
                for g in x:
        
                    f2.write(''+str(g)+' '+str(op[g])+'\n')
        else:
            f2.write(''+ 'no' + '\n')
    else:

        f2.write(''+ 'no' + '\n')   


    f1.close()
    f2.close()

if __name__ == '__main__':
    main()