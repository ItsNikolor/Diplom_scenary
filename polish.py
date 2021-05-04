def str_polish(s, game):
    return ' '.join(to_reverse_polish(s, game))


def to_reverse_polish(s, game, raise_exception=False):
    try:
        s = s.strip()
        s = s.replace(' ', '')
        s = s.replace('\t', '')

        for _ in range(20):
            s = s.replace('\n\n', '\n')  # Сделать почеловечески

        s = s.replace('\n', '&')

        if '{' in s or '}' in s or '#' in s:
            raise Exception('{}# являются запрещёнными символами')

        s = '(' + s + ')'

        priority = dict([
            ('+', 1),
            ('-', 1),
            ('*', 2),
            ('/', 2),
            ('//', 2),
            ('%', 2),
            ('>', 1),
            ('<', 1),
            ('=', 1),
            ('>=', 1),
            ('<=', 1),
            ('&', 0),
            ('|', 0),
            ('(', -1),
            (')', -1),
            ('{', -1)
        ])

        operations = set(priority.keys())

        max_op = max(map(lambda x: len(x), operations))

        av_ind = []
        for key in game.cur_infos.keys():
            if ((key[0] == 'p' and '_' not in key) or
                    key[0] == 't' or
                    key[0] == 'r'):
                av_ind.extend(game.cur_infos[key].keys())
        av_ind = set(av_ind)
        av_ind.add('an')

        funcs = dict([
            ('not', 1),
            ('exp', 1),
            ('ans', 1),
            ('show', 2),
            ('eq', 2),
            ('minus', 1),
            ('max', 2),
            ('min', 2),
        ])

        av_func = set(funcs.keys())

        def closest_op(string, begin_i):
            for begin_ind in range(begin_i, len(string)):
                for offset in range(max_op, 0, -1):
                    if string[begin_ind:begin_ind + offset] in operations:
                        return begin_ind, string[begin_ind:begin_ind + offset]
            return -1, None

        stack = []
        ops = []

        count_arg = []

        i = 0
        while i < len(s):
            ind, op = closest_op(s, i)
            if ind == -1:
                pass  # impossible

            if ind != i:
                if s[i:ind] in av_ind:
                    stack.append(s[i:ind])
                elif s[i:ind] in av_func:
                    assert op == '('
                    op = '{'
                    ops.append(s[i:ind])

                    count_arg.append(0)
                    if s[i:ind] == 'show':
                        i = s.find(',', ind + 1)
                        assert i > ind + 1
                        int(s[ind + 1:i])
                        stack.append(s[ind + 1:i])
                        k = s.find(')', i + 1)
                        assert k > i + 1
                        args = s[i + 1:k].split(',')
                        assert len(args) > 0
                        assert all(map(lambda x: x[0] == 't' and x in av_ind, args))
                        stack.append(','.join(args))

                        ops.append('{')
                        op = ')'
                        ind = k
                        count_arg[-1] = 1

                    elif s[i:ind] == 'eq':
                        i = s.find(',', ind + 1)
                        assert i > ind + 1
                        p = s[ind + 1:i]
                        assert p[0] == 'p' and '_' not in p

                        ops.append('{')
                        stack.append(p)
                        op = ','
                        ind = i
                    elif s[i:ind] == 'ans':
                        i = s.find(')', ind + 1)
                        assert i > ind + 1
                        p = s[ind + 1:i]
                        assert p[0] == 'r' and '_' in p  # redundant
                else:
                    float(s[i:ind])
                    stack.append(s[i:ind])
            else:
                assert op == ')' or op == '(' or s[ind - 1] == ')' or op == '-' or stack[-1] in av_func
                if op == '-':
                    if s[ind + 1] != '(':
                        k, o = closest_op(s, ind + 1)
                        assert k > ind + 1

                        if o == '(':
                            assert s[ind + 1:k] in av_func
                            counter = 1
                            k += 1
                            while counter != 0:
                                if s[k] == '(':
                                    counter += 1
                                elif s[k] == ')':
                                    counter -= 1
                                    if k == len(s) - 1 and counter != 0:
                                        raise Exception('Плохой баланс скобок')
                                k += 1
                        s = s[:ind + 1] + '(' + s[ind + 1:k] + ')' + s[k:]

                    s = s[:ind] + 'minus' + s[ind + 1:]
                    continue

            if op == ',':
                assert len(count_arg) > 0
                while ops[-1] != '{':
                    assert ops[-1] != '('
                    stack.append(ops.pop())
                count_arg[-1] += 1
            elif op == '(' or op == '{':
                if op == '(':
                    assert i == 0 or (ind == i and s[i - 1] != ')')
                ops.append(op)
            elif op == ')':
                while ops[-1] != '{' and ops[-1] != '(':
                    stack.append(ops.pop())
                if ops.pop() == '{':
                    count_arg[-1] += 1
                    assert funcs[ops[-1]] == count_arg[-1]
                    stack.append(ops.pop())
                    count_arg.pop()
            else:
                while priority[ops[-1]] >= priority[op]:
                    stack.append(ops.pop())
                ops.append(op)

            i = ind + len(op)

        assert i == len(s)
        assert len(ops) == 0

        return stack

    except Exception as e:
        print(e)
        if raise_exception:
            raise e
        return None
