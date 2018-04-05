
class ProbDist:
    def __init__(self, varname, freqs=None):
        self.prob = {}
        self.varname = varname
        self.values = []
        if freqs:
            for (v, p) in freqs.items():
                self[v] = p
            self.normalize()

    def __getitem__(self, val):
        "Given a value, return P(value)."
        try:
            return self.prob[val]
        except KeyError:
            return 0

    def __setitem__(self, val, p):
        "Set P(val) = p."
        if val not in self.values:
            self.values.append(val)
        self.prob[val] = p

    def normalize(self):
        total = sum(self.prob.values())
        if total != 1:
            for val in self.prob:
                self.prob[val] /= total
        return self

    def show_approx(self, numfmt='%.2g'):
        """Show the probabilities rounded and sorted by key, for the
        sake of portable doctests."""
        return ', '.join([('%s: ' + numfmt) % (v, p)
                          for (v, p) in sorted(self.prob.items())])

    def __repr__(self):
        return "P(%s)" % self.varname

# ______________________________________________________________________________

class BayesNet:

    def __init__(self, node_specs = []):
        "nodes ordered with parents before children."

        self.nodes = []
        self.chance_vars = []
        self.decision_vars = []
        self.utility_vars = []
        self.variables = []

        for node_spec in node_specs:
            self.add(node_spec)

    def add(self, node_spec):
        node = BayesNode(*node_spec)
        assert node.variable not in self.variables
        assert all((parent in self.variables) for parent in node.parents)
        self.nodes.append(node)
        if node.kind == 'chance':
            self.chance_vars.append(node.variable)
            self.variables.append(node.variable)
        elif node.kind == 'decision':
            self.decision_vars.append(node.variable)
            self.variables.append(node.variable)
        elif node.kind == 'utility':
            self.utility_vars.append(node.variable)
        for parent in node.parents:
            self.variable_node(parent).children.append(node)

    def variable_node(self, var):
        for n in self.nodes:
            if n.variable == var:
                return n
        raise Exception("Don't have that variable: %s" % var)

    def variable_values(self, var):
        return [True, False]

    def __repr__(self):
        return 'BayesNet(%r)' % self.nodes


# ______________________________________________________________________________


class BayesNode:

    def __init__(self, kind, X, parents, cpt):

        if kind == 'chance':
            if isinstance(parents, str):
                parents = parents.split()
            if isinstance(cpt, (float,int)):
                cpt = {(): cpt}
            elif isinstance(cpt, dict):
                if cpt and isinstance(list(cpt.keys())[0], bool):
                    cpt = {(v,): p for v, p in cpt.items()}

            assert isinstance(cpt, dict)
            for vs, p in cpt.items():
                assert isinstance(vs, tuple) and len(vs) == len(parents)
                assert all(isinstance(v, bool) for v in vs)
                assert 0 <= p <= 1

            self.kind = 'chance'
            self.variable = X
            self.parents = parents
            self.cpt = cpt
            self.children = []

        elif kind == 'decision':
            if isinstance(parents, str):
                parents = parents.split()
            self.kind = 'decision'
            self.variable = X
            self.parents = parents
            self.children = []

        elif kind == 'utility':
            if isinstance(parents, str):
                parents = parents.split()
            if isinstance(cpt, dict):
                if cpt and isinstance(list(cpt.keys())[0], bool):
                    cpt = {(v,): p for v, p in cpt.items()}
            assert isinstance(cpt, dict)
            for vs, p in cpt.items():
                assert isinstance(vs, tuple) and len(vs) == len(parents)
                assert all(isinstance(v, bool) for v in vs)
            self.kind = 'utility'
            self.variable = X
            self.parents = parents
            self.cpt = cpt
            self.children = []

    def p(self, value, event):
        assert isinstance(value, bool)
        ptrue = self.cpt[event_values(event, self.parents)]
        if value is True:
            return ptrue
        else:
            return 1 - ptrue

    def __repr__(self):
        return repr((self.variable, ' '.join(self.parents)))


# ______________________________________________________________________________


def enumeration_ask(X, e, bn):

    assert X not in e, "Query variable must be distinct from evidence"
    Q = ProbDist(X)
    for xi in bn.variable_values(X):
        Q[xi] = enumerate_all(bn.variables, extend(e, X, xi), bn)
    return Q.normalize()


def enumerate_all(variables, e, bn):

    if not variables:
        return 1.0
    Y, rest = variables[0], variables[1:]
    Ynode = bn.variable_node(Y)
    if Y in e:
        return Ynode.p(e[Y], e) * enumerate_all(rest, e, bn)
    else:
        return sum(Ynode.p(y, e) * enumerate_all(rest, extend(e, Y, y), bn)
                   for y in bn.variable_values(Y))


# ______________________________________________________________________________


class Factor:
    def __init__(self, variables, cpt):
        self.variables = variables
        self.cpt = cpt

    def pointwise_product(self, other, bn):
        "Combine two factors."
        variables = list(set(self.variables) | set(other.variables))
        cpt = {event_values(e, variables): self.p(e) * other.p(e)
               for e in all_events(variables, bn, {})}
        return Factor(variables, cpt)

    def sum_out(self, var, bn):
        "Eliminating var of factor."
        variables = [X for X in self.variables if X != var]
        cpt = {event_values(e, variables): sum(self.p(extend(e, var, val))
                                               for val in bn.variable_values(var))
               for e in all_events(variables, bn, {})}
        return Factor(variables, cpt)

    def normalize(self):
        "Return my probabilities; must be down to one variable."
        #assert len(self.variables) == 1
        return ProbDist(self.variables,
                        {k: v for k, v in self.cpt.items()})

    def p(self, e):
        "Look up my value tabulated for e."
        return self.cpt[event_values(e, self.variables)]


def elimination_ask(X, e, bn):

    for x in X:
        assert x not in e

    for ed in e:
        if ed in bn.decision_vars:
            node = bn.variable_node(ed)
            if e[ed] is True:
                node.cpt = {(): 1}
            else:
                node.cpt = {(): 0}
    factors = []
    for var in reversed(bn.variables):
        factors.append(make_factor(var, e, bn))
        if is_hidden(var, X, e):
            factors = sum_out(var, factors, bn)
    return pointwise_product(factors, bn).normalize()


def adjust_seq(a, b):
    list_temp = []
    for name in a:
        for i in range(len(b)):
            if name == b[i]:
                list_temp.append(i)
    return list_temp


def elimination_ask_utility(e, bn):
    utility_node = bn.variable_node('utility')
    tmp = [val for val in utility_node.parents if val not in e]
    tmp2 = [val for val in utility_node.parents if val in e]
    Prob = elimination_ask(tmp, e, bn)
    sum = 0
    list_temp = [True] * len(utility_node.parents)

    for x in tmp2:
        for i in range(len(utility_node.parents)):
            if utility_node.parents[i] == x:
                list_temp[i] = e[x]

    for y in Prob.prob:
        for i in range(len(Prob.varname)):
            for j in range(len(utility_node.parents)):
                if Prob.varname[i] == utility_node.parents[j]:
                    list_temp[j] = y[i]
        t = tuple(list_temp)
        sum += Prob.prob[y] * utility_node.cpt[t]
    return sum


def elimination_ask_max_utility(X, e, bn):
    e_max = {}
    max = -10000000
    for e1 in all_events(X, bn, e):
        value = elimination_ask_utility(e1, bn)
        if value > max:
            e_max = e1
            max = value

    result = []
    for x in e_max:
        if x in e:
            pass
        elif e_max[x] == True:
            result.append('+')
        elif e_max[x] == False:
            result.append('-')
        else:
            print 'Something wrong'
    result.append(str(int(round(max))))

    return ' '.join(result)


def elimination_ask_kinds(q, bn):
    if q.type == 'P':
        result = elimination_ask(q.X, q.e, bn)
        varname = result.varname
        seq = adjust_seq(varname, q.X)
        list_temp = []
        for i in seq:
            list_temp.append(q.value[i])
        t = tuple(list_temp)
        return '%.2f' % result[t]
    elif q.type == 'EU':
        return str(int(round(elimination_ask_utility(q.e, bn))))
    elif q.type == 'MEU':
        return elimination_ask_max_utility(q.X, q.e, bn)


def is_hidden(var, X, e):
    return var not in X and var not in e


def make_factor(var, e, bn):
    """Return the factor for var in bn's joint distribution given e.
    That is, bn's full joint distribution, projected to accord with e,
    is the pointwise product of these factors for bn's variables."""
    node = bn.variable_node(var)
    variables = [X for X in [var] + node.parents if X not in e]
    cpt = {event_values(e1, variables): node.p(e1[var], e1)
           for e1 in all_events(variables, bn, e)}
    return Factor(variables, cpt)


def pointwise_product(factors, bn):
    return reduce(lambda f, g: f.pointwise_product(g, bn), factors)


def sum_out(var, factors, bn):
    "Eliminate var from all factors by summing over its values."
    result, var_factors = [], []
    for f in factors:
        (var_factors if var in f.variables else result).append(f)
    result.append(pointwise_product(var_factors, bn).sum_out(var, bn))
    return result


def event_values(event, variables):
    if isinstance(event, tuple) and len(event) == len(variables):
        return event
    else:
        return tuple([event[var] for var in variables])


def extend(s, var, val):
    "Copy the substitution s and extend it by setting var to val; return copy."
    s2 = s.copy()
    s2[var] = val
    return s2


def all_events(variables, bn, e):
    "Yield every way of extending e with values for all variables."
    if not variables:
        yield e
    else:
        X, rest = variables[0], variables[1:]
        for e1 in all_events(rest, bn, e):
            for x in bn.variable_values(X):
                yield extend(e1, X, x)


# ______________________________________________________________________________


class Query():
    def __init__(self, type, X, value, e):
        self.type = type
        self.X = X
        self.value = value
        self.e = e


def readfile():
    Querys = []
    BayesNet = []
    with open('input.txt', 'r') as infile:
        lines = infile.readlines()
        for i in xrange(len(lines)):
            lines[i] = lines[i].strip('\n')

        line_num = 0

        while lines[line_num] != '******':
            X = []
            value = []
            e = {}
            if lines[line_num][0] == 'P':
                items = lines[line_num][1:].strip('\n').strip('(').strip(')').split(' ')
                for i in range(len(items)):
                    items[i] = items[i].strip(',')
                index = 0
                while index < len(items) and items[index] is not '|':
                    X.append(items[index])
                    if items[index + 2] is '+':
                        value.append(True)
                    elif items[index + 2] is '-':
                        value.append(False)
                    else:
                        print 'input wrong'
                    index += 3

                if index < len(items) and items[index] is '|':
                    index += 1
                    while index < len(items):
                        if items[index + 2] == '+':
                            e[items[index]] = True
                        elif items[index + 2] == '-':
                            e[items[index]] = False
                        else:
                            print 'input wrong'
                        index += 3
                Querys.append(Query('P',X,value,e))
            elif lines[line_num][0:2] == 'EU':
                items = lines[line_num][2:].strip('\n').strip('(').strip(')').split(' ')
                for i in range(len(items)):
                    items[i] = items[i].strip(',')
                index = 0
                while index < len(items) and items[index] is not '|':
                    if items[index + 2] is '+':
                        e[items[index]] = True
                        value.append(True)
                    elif items[index + 2] is '-':
                        e[items[index]] = False
                    else:
                        print 'input wrong'
                    index += 3

                if index < len(items) and items[index] is '|':
                    index += 1
                    while index < len(items):
                        if items[index + 2] == '+':
                            e[items[index]] = True
                        elif items[index + 2] == '-':
                            e[items[index]] = False
                        else:
                            print 'input wrong'
                        index += 3
                Querys.append(Query('EU', X, value, e))
            elif lines[line_num][0:3] == 'MEU':
                items = lines[line_num][3:].strip('\n').strip('(').strip(')').split(' ')
                for i in range(len(items)):
                    items[i] = items[i].strip(',')
                index = 0
                while index < len(items) and items[index] is not '|':
                    X.append(items[index])
                    index += 1
                if index < len(items) and items[index] is '|':
                    index += 1
                    while index < len(items):
                        if items[index + 2] == '+':
                            e[items[index]] = True
                        elif items[index + 2] == '-':
                            e[items[index]] = False
                        else:
                            print 'input wrong'
                        index += 3
                Querys.append(Query('MEU', X, value, e))

            line_num += 1

        while line_num < len(lines) and (lines[line_num] == '***' or lines[line_num] == '******'):
            line_num += 1
            X = ''
            parents = ''
            cpt = {}
            items = lines[line_num].split(' ')
            if items[0] == 'utility':
                X = items[0]
                parents = ' '.join(items[2:])
                line_num += 1
                while line_num < len(lines) and lines[line_num] != '***' and lines[line_num] != '******':
                    prob_tab = lines[line_num].split(' ')
                    list_temp = []
                    for i in range(1, len(prob_tab)):
                        if prob_tab[i] == '+':
                            list_temp.append(True)
                        elif prob_tab[i] == '-':
                            list_temp.append(False)
                        else:
                            print 'input wrong'
                    t1 = ()
                    t1 = tuple(list_temp)
                    cpt[t1] = float(prob_tab[0])
                    line_num += 1
                BayesNet.append(('utility', X, parents, cpt))

            elif len(items) == 1:
                X = items[0]
                parents = ''
                if lines[line_num + 1] == 'decision':
                    BayesNet.append(('decision', X, parents, cpt))
                else:
                    cpt = {(): float(lines[line_num + 1])}
                    BayesNet.append(('chance', X, parents, cpt))
                line_num += 2
            else:
                X = items[0]
                parents = ' '.join(items[2:])
                line_num += 1
                while line_num < len(lines) and lines[line_num] != '***' and lines[line_num] != '******':
                    prob_tab = lines[line_num].split(' ')
                    list_temp = []
                    for i in range(1, len(prob_tab)):
                        if prob_tab[i] == '+':
                            list_temp.append(True)
                        elif prob_tab[i] == '-':
                            list_temp.append(False)
                        else:
                            print 'input wrong'
                    t1 = ()
                    t1 = tuple(list_temp)
                    cpt[t1] = float(prob_tab[0])
                    line_num += 1
                BayesNet.append(('chance', X, parents, cpt))

        return Querys, BayesNet

# ______________________________________________________________________________



def main():

    qs , bn = readfile()
    bayesnet = BayesNet(bn)
    output = []

    for q in qs:
        output.append(elimination_ask_kinds(q, bayesnet))

    with open('output.txt', 'wb') as outfile:

        outfile.write('\n'.join(output))


main()
