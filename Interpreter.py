import Instructions
import AscendentParser
import DescendentParser
from Expressions import *
from Table import Symbol
from Table import SymbolTable
from PyQt5.QtWidgets import QInputDialog, QLineEdit
from PyQt5.QtCore import QDir

symbol_table = SymbolTable()
label_table = SymbolTable()
instructions_stack = []  # indice 0 es la cabeza
actual_label = None
console_value = ''


def process_labels(labels):
    for label in labels:
        label.type = REG_TYPE.CONTROL
        label_table.add(label.name, label)


def process_instructions():
    global instructions_stack
    while len(instructions_stack) != 0:
        instr = instructions_stack.pop(0)
        if isinstance(instr, Instructions.Assignation):
            if isinstance(instr.reg, Register):
                process_normal_assignation(instr)
            elif isinstance(instr.reg, ArrayRegister):
                process_array_assignation(instr)
        elif isinstance(instr, Instructions.Print):
            process_print(instr)
        elif isinstance(instr, Instructions.If):
            process_if(instr)
        elif isinstance(instr, Instructions.GoTo):
            process_goto(instr)
        elif isinstance(instr, Instructions.Unset):
            process_unset(instr)
        elif isinstance(instr, Instructions.Exit):
            process_exit()


def process_normal_assignation(instr):
    'contains a register and an expression'
    primitive = process_expression(instr.expr)
    try:
        symb = Symbol(instr.reg.name, instr.reg.type,
                      primitive.type, primitive.value)
        symbol_table.add(instr.reg.name, symb)
        global actual_label
        if not actual_label.type_defined and symb.reg_type == REG_TYPE.RETURN_VALUE:
            actual_label.type = REG_TYPE.FUNCTION
            actual_label.type_defined = True
    except AttributeError as e:
        print('*FALLO EN LA ASIGNACION*\nNO SE PUEDE REALIZAR LA ASIGNACIÓN DE', instr.reg.name)
        print(e)


def process_array_assignation(instr):
    'contains an array register and an expression'
    # objeto tipo Primitive que contiene los valores para la asignacion
    expression = process_expression(instr.expr)
    try:
        array_reg = instr.reg  # objeto ArrayRegister
        index_list = array_reg.index_list  # lista de indices del arreglo
        reg = array_reg.reg  # objeto Register
        # se obtiene el simbolo de un arreglo. en el se encuentra el diccionario que representa el arreglo (symbol_array.value)
        symbol_array = symbol_table.get(reg.name)
        i = 1
        name = reg.name  # se almacena el nombre del registro
        # bracket representa a uno de los indices de la lista
        for bracket in index_list:
            # contiene el primitivo con el cual se acceden a los valores del arreglo
            index = process_terminal(bracket).value
            # si no es el ultimo indice...
            if i != len(index_list):
                # se intenta obtener el simbolo del diccionario
                next_array = symbol_array.value.get(index, None)
                i = i+1
                name = name+'['+str(index)+']'
                # si no lo encuentra se debe de crear uno
                if next_array == None:
                    next_array = Symbol(name, reg.type, TYPE.ARRAY, {})
                # y se asigna el nuevo symbol_array
                symbol_array = next_array
            else:
                name = name+'['+str(index)+']'
                if isinstance(symbol_array.value, dict):
                    symbol_array.value[index] = Symbol(
                        name, reg.type, expression.type, expression.value)
                elif isinstance(symbol_array.value, str):
                    string = list(symbol_array.value)
                    string[index] = expression.value
                    symbol_array.value = "".join(string)
                else:
                    raise Exception
    except Exception as e:
        'No es un arreglo o no se encontró'
        print('*Fallo en la asignación*\nNo se puede realizar la asignación de \'' +
              instr.reg.reg.name+'\'')
        print(e)


def process_expression(expr):
    if isinstance(expr, Terminal):
        return process_terminal(expr)
    elif isinstance(expr, BinaryExpression):
        op1 = process_terminal(expr.op1)
        op2 = process_terminal(expr.op2)
        return process_binary_expression(expr.operation, op1, op2)
    elif isinstance(expr, UnitExpression):
        operand = process_terminal(expr.operand)
        return process_unit_expression(expr.operation, operand)


def process_unit_expression(operation, operand):
    operations = {
        UNIT_OPERATION.NEGATIVE: process_negative,
        UNIT_OPERATION.POINTER: process_pointer,
        UNIT_OPERATION.ABSOLUTE: process_absolute,
        LOGIC_OPERATION.NOT: process_not,
        BIT_OPERATION.NOT: process_bit_not,
    }
    operation = operations.get(operation, lambda: print("operador invalido"))
    try:
        return operation(operand)
    except UnboundLocalError:
        print('*TIPO NO VÁLIDOS*\n' +
              'No es posible realizar la operación \''+operation.name+'\'')
        print('Tipo: \''+operand.type.name+'\'')


def process_negative(operand):
    if operand.type == TYPE.INTEGER or operand.type == TYPE.DECIMAL:
        value = - operand.value
    return Primitive('', operand.type, value)


def process_pointer(operand):
    return Primitive('', operand.type, operand.value)


def process_absolute(operand):
    return Primitive('', operand.type, abs(operand.value))


def process_not(operand):
    if (operand.type == TYPE.INTEGER):
        if operand.value == 1:
            value = 0
        elif operand.value == 0:
            value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_bit_not(operand):
    value = ~ operand.value
    return Primitive('', TYPE.INTEGER, value)


def process_binary_expression(operation, op1, op2):
    operations = {
        ARITHMETIC_OPERATION.SUM: process_sum,
        ARITHMETIC_OPERATION.SUBSTRACTION: process_substraction,
        ARITHMETIC_OPERATION.MULTIPLICATION: process_multiplication,
        ARITHMETIC_OPERATION.DIVISION: process_division,
        ARITHMETIC_OPERATION.MODULE: process_module,
        LOGIC_OPERATION.OR: process_or,
        LOGIC_OPERATION.AND: process_and,
        LOGIC_OPERATION.XOR: process_xor,
        RELATIONAL_OPERATION.COMPARISSON: process_comparisson,
        RELATIONAL_OPERATION.DISTINCT: process_distinct,
        RELATIONAL_OPERATION.LESS_EQUAL: process_less_equal,
        RELATIONAL_OPERATION.GREATER_EQUAL: process_greater_equal,
        RELATIONAL_OPERATION.LESS: process_less,
        RELATIONAL_OPERATION.GREATER: process_greater,
        BIT_OPERATION.AND: process_bit_and,
        BIT_OPERATION.OR: process_bit_or,
        BIT_OPERATION.XOR: process_bit_xor,
        BIT_OPERATION.L_SHIFT: process_bit_left_shift,
        BIT_OPERATION.R_SHIFT: process_bit_right_shift,
    }
    function = operations.get(operation, lambda: print("operador invalido"))
    try:
        return function(op1, op2)
    except:
        try:
            print('*TIPOS NO VÁLIDOS*\n' +
                  'No es posible realizar la operación \''+operation.name+'\'')
            # Si no se pudo realizar la operacion es por la compatibilidad de tipos...
            print('Tipos: \''+op1.type.name+'\' y \''+op2.type.name+'\'')
        except AttributeError:
            # ... o es porque se obtuvo un None
            print('Se obtuvo un valor None')
        return None


def process_sum(op1, op2):
    if (op1.type == TYPE.INTEGER and op2.type == TYPE.INTEGER) or (op1.type == TYPE.DECIMAL and op2.type == TYPE.DECIMAL) or (op1.type == TYPE.STRING and op2.type == TYPE.STRING):
        _type = op1.type
        value = op1.value + op2.value
    elif (op1.type == TYPE.CHARACTER and op2.type == TYPE.CHARACTER) or (op1.type == TYPE.CHARACTER and op2.type == TYPE.STRING) or (op1.type == TYPE.STRING and op2.type == TYPE.CHARACTER):
        _type = TYPE.STRING
        value = op1.value + op2.value
    elif (op1.type == TYPE.INTEGER and op2.type == TYPE.DECIMAL) or (op1.type == TYPE.DECIMAL and op2.type == TYPE.INTEGER):
        _type = TYPE.DECIMAL
        value = op1.value + op2.value
    return Primitive('', _type, value)


def process_substraction(op1, op2):
    if op1.type == TYPE.INTEGER and op2.type == TYPE.INTEGER:
        _type = TYPE.INTEGER
        value = op1.value - op2.value
    elif (op1.type == TYPE.INTEGER and op2.type == TYPE.DECIMAL) or (op1.type == TYPE.DECIMAL and op2.type == TYPE.INTEGER):
        _type = TYPE.DECIMAL
        value = op1.value - op2.value
    return Primitive('', _type, value)


def process_multiplication(op1, op2):
    if op1.type == TYPE.INTEGER and op2.type == TYPE.INTEGER:
        _type = TYPE.INTEGER
        value = op1.value * op2.value
    elif (op1.type == TYPE.INTEGER and op2.type == TYPE.DECIMAL) or (op1.type == TYPE.DECIMAL and op2.type == TYPE.INTEGER):
        _type = TYPE.DECIMAL
        value = op1.value * op2.value
    return Primitive('', _type, value)


def process_division(op1, op2):
    if op1.type == TYPE.INTEGER and op2.type == TYPE.INTEGER:
        value = op1.value / op2.value
        if op1.value % op2.value == 0:
            _type = TYPE.INTEGER
        else:
            _type = TYPE.DECIMAL
    elif (op1.type == TYPE.INTEGER and op2.type == TYPE.DECIMAL) or (op1.type == TYPE.DECIMAL and op2.type == TYPE.INTEGER):
        _type = TYPE.DECIMAL
        value = op1.value / op2.value
    return Primitive('', _type, value)


def process_module(op1, op2):
    if (op1.type == TYPE.INTEGER and op2.type == TYPE.INTEGER) or (op1.type == TYPE.INTEGER and op2.type == TYPE.DECIMAL) or (op1.type == TYPE.DECIMAL and op2.type == TYPE.INTEGER):
        value = op1.value % op2.value
    return Primitive('', TYPE.INTEGER, value)


def process_or(op1, op2):
    value = 0
    if (op1.value == 1 or op2.value == 1):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_and(op1, op2):
    value = 0
    if (op1.value == 1 and op2.value == 1):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_xor(op1, op2):
    value = 0
    if (op1.value == 1 and op2.value == 0) or (op1.value == 0 and op2.value == 1):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_comparisson(op1, op2):
    value = 0
    if (op1.value == op2.value):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_distinct(op1, op2):
    value = 0
    if (op1.value != op2.value):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_less_equal(op1, op2):
    value = 0
    if (op1.value <= op2.value):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_greater_equal(op1, op2):
    value = 0
    if (op1.value >= op2.value):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_less(op1, op2):
    value = 0
    if (op1.value < op2.value):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_greater(op1, op2):
    value = 0
    if (op1.value > op2.value):
        value = 1
    return Primitive('', TYPE.INTEGER, value)


def process_bit_and(op1, op2):
    value = op1.value & op2.value
    return Primitive('', TYPE.INTEGER, value)


def process_bit_or(op1, op2):
    value = op1.value | op2.value
    return Primitive('', TYPE.INTEGER, value)


def process_bit_xor(op1, op2):
    value = op1.value ^ op2.value
    return Primitive('', TYPE.INTEGER, value)


def process_bit_left_shift(op1, op2):
    value = op1.value << op2.value
    return Primitive('', TYPE.INTEGER, value)


def process_bit_right_shift(op1, op2):
    value = op1.value >> op2.value
    return Primitive('', TYPE.INTEGER, value)


def process_terminal(term):
    if isinstance(term, Primitive):
        return term
    elif isinstance(term, Register):
        try:
            # es el registro recuperado como símbolo
            symbol = symbol_table.get(term.name)
            global actual_label
            '''si no ha sido definido el tipo y el tipo del registro es parametro o retorno de nivel se establece el tipo como PROCEDURE
            pero no se establece como tipo ya definido porque puede verse afectado por el uso de un valor de retorno y ser FUNCTION.
            *se realizó de esta manera ya que se está utilizando un parametro o retorno de nivel en una instrucción que lo requiera,
            así que al procesar el registro simple y coincidir los tipos se le asigna el tipo como Procedimiento'''
            if not actual_label.type_defined and (symbol.reg_type == REG_TYPE.PARAMETER or symbol.reg_type == REG_TYPE.RETURN_LEVEL):
                actual_label.type = REG_TYPE.PROCEDURE
            return Primitive('', symbol.value_type, symbol.value)
        except AttributeError:
            print("*Error al recuperar registro*\nNo se ha definido '"+term.name+"'")
            return None
    elif isinstance(term, ArrayRegister):
        'Se está accediendo al índice de un arreglo'
        try:
            reg = term.reg  # es el Register que contiene el objeto ArrayRegister
            index_list = term.index_list  # lista de indices del ArrayRegister
            # se obtiene de la tabla de simbolos el registro que actua como arreglo
            symbol_array = symbol_table.get(reg.name)
            array = symbol_array.value  # es el diccionario que actua como arreglo del registro
            i = 1
            # bracket representa a un terminal de la lista de indices
            for bracket in index_list:
                # index representa el valor de un Primitive
                index = process_terminal(bracket).value
                if i != len(index_list):
                    # si no es el ultimo indice en la lista significa que se obtendra un simbolo de tipo ARRAY y sigue siendo un diccionario
                    array = array.get(index, None)
                    i = i+1
                else:
                    try:
                        # si es el ultimo indice, el diccionario devolvera un valor simbolo distinto (INTEGER, CHARACTER, etc.)
                        symbol = array.get(index, None)
                        return Primitive('', symbol.value_type, symbol.value)
                    except AttributeError:
                        # pero si se está intentando acceder a la posición de un String se debe de verificar y devolver el valor respectivo
                        if isinstance(array.value, str):
                            return Primitive('', TYPE.CHARACTER, array.value[index])
                        else:  # si no cumple entonces sí es un error
                            raise Exception
        except Exception as e:
            'Al producirse una exception se detiene la busqueda del arreglo, ya que no existe'
            print(
                '*Error al obtener arreglo*\nNo se ha encontrado el indice solicitado para \''+reg.name+'\'')
            return None
    elif isinstance(term, Array):
        'Un arreglo está siendo creado'
        return Primitive('', TYPE.ARRAY, {})
    elif isinstance(term, Conversion):
        try:
            return process_conversion(term)
        except Exception as e:
            print('*Error en conversion*')
            print(e)
            return None
    elif isinstance(term, Read):
        text, ok = QInputDialog().getText(None, "read()",
                                          "Ingresa el valor:", QLineEdit.Normal,
                                          QDir().home().dirName())
        if ok and text:
            return Primitive('', TYPE.STRING, str(text))
        return None
        


def process_conversion(expr):
    symb = symbol_table.get(expr.reg.name)
    if symb.value_type != TYPE.ARRAY:
        'es un registro normal'
        if expr.type == TYPE.INTEGER:
            return convert_int(symb)
        elif expr.type == TYPE.DECIMAL:
            return convert_float(symb)
        elif expr.type == TYPE.CHARACTER:
            return convert_char(symb)
    else:
        'es un registro de arreglos'
        array = symb.value  # es el diccionario del registro
        # recorrerá dentro de los diccionarios para obtener el valor primitivo del primer índice
        while True:
            'es un diccionario, se debe de obtener el primer simbolo'
            x = list(array)[0:1]
            array = array[x[0]]  # este es el primer simbolo de array
            if not isinstance(array.value, dict):
                'ya no es un diccionario'
                break
        symbol = array  # este ya es el simbolo que contiene el valor primitivo para realizar las conversiones
        if expr.type == TYPE.INTEGER:
            return convert_int(symbol)
        elif expr.type == TYPE.DECIMAL:
            return convert_float(symbol)
        elif expr.type == TYPE.CHARACTER:
            return convert_char(symbol)


def convert_int(symb):
    if symb.value_type == TYPE.INTEGER:
        return Primitive('', TYPE.INTEGER, int(symb.value))
    elif symb.value_type == TYPE.DECIMAL:
        return Primitive('', TYPE.INTEGER, int(symb.value))
    elif symb.value_type == TYPE.CHARACTER:
        return Primitive('', TYPE.INTEGER, ord(symb.value))
    elif symb.value_type == TYPE.STRING:
        return Primitive('', TYPE.INTEGER, ord(symb.value[0]))


def convert_float(symb):
    if symb.value_type == TYPE.INTEGER:
        return Primitive('', TYPE.DECIMAL, float(symb.value))
    elif symb.value_type == TYPE.DECIMAL:
        return Primitive('', TYPE.DECIMAL, float(symb.value))
    elif symb.value_type == TYPE.CHARACTER:
        return Primitive('', TYPE.DECIMAL, float(ord(symb.value)))
    elif symb.value_type == TYPE.STRING:
        return Primitive('', TYPE.DECIMAL, float(ord(symb.value[0])))


def convert_char(symb):
    if symb.type == TYPE.INTEGER:
        if symb.value >= 0 and symb.value <= 255:
            return Primitive('', TYPE.CHARACTER, chr(symb.value))
        else:
            value = symb.value % 256
            return Primitive('', TYPE.CHARACTER, chr(value))
    elif symb.type == TYPE.DECIMAL:
        if symb.value >= 0 and symb.value <= 255:
            return Primitive('', TYPE.CHARACTER, chr(int(symb.value)))
        else:
            value = symb.value % 256
            return Primitive('', TYPE.CHARACTER, chr(value))
    elif symb.type == TYPE.CHARACTER:
        return Primitive('', TYPE.CHARACTER, symb.value)
    elif symb.type == TYPE.STRING:
        return Primitive('', TYPE.DECIMAL, symb.value[0])


def process_if(instr):
    '''al procesar un if se podría establecer el tipo de la etiqueta como Control
    pero al principio de la ejecución ya fueron definidas toda las etiquetas como Control
    por lo que se omite aquí'''
    expr = process_expression(instr.expr)
    if expr.value == 1:
        process_goto(instr.goto)


def process_goto(instr):
    label = label_table.get(instr.label)
    if label != None:
        global instructions_stack, actual_label
        # se limpia la pila ya que el salto 'goto' indica que se tienen que ejecutar únicamente las instrucciones de esa etiqueta a la que se hace el salto
        instructions_stack = [] + label.instructions
        actual_label = label
    else:
        print("*Error en goto*")
        print("No es posible hacer un salto a \'" +
              instr.label+"\'. No fue definido.")


def process_print(instr):
    try:
        content = process_terminal(instr.content)
        global console_value
        if str(content.value) == '\\n':
            console_value = console_value + '>>\n'
        else:
            console_value = console_value + '>> '+str(content.value) + '\n'
    except:
        print('*Fallo en print()*\nNo es posible imprimir', str(instr.content))


def process_exit():
    raise InterruptedError


def process_unset(instr):
    if isinstance(instr.reg, Register):
        try:
            del symbol_table.symbols[instr.reg.name]
        except KeyError:
            print(
                '*Fallo en unset()*\nNo se encontró un valor para el registro\''+instr.reg.name+'\'')
    elif isinstance(instr.reg, ArrayRegister):
        name = ''
        try:
            array_reg = instr.reg  # se guarda el ArrayRegister del  unset...
            reg = array_reg.reg  # ... el cual contiene un objeto de tipo Register
            # la lista de indices se obtiene del ArrayRegister
            index_list = array_reg.index_list
            # se solicita a la tabla de simbolos el simbolo con el nombre del registro y se obtiene el diccionario del registro
            array = symbol_table.get(reg.name).value
            i = 1
            name = reg.name
            # bracket representa a un terminal de la lista de indices
            for bracket in index_list:
                # index representa el valor de un Primitive
                index = process_terminal(bracket).value
                if i != len(index_list):
                    # si no es el ultimo indice en la lista significa que se obtendra un simbolo de tipo ARRAY y sigue siendo un diccionario
                    array = array.get(index, None)
                    i = i+1
                    name = name+'['+str(index)+']'
                else:
                    # si es el ultimo indice, el diccionario devolvera un valor simbolo distinto (INTEGER, CHARACTER, etc.)
                    # y este es el que es eliminado
                    name = name+'['+str(index)+']'
                    del array[index]
        except:
            print(
                "*Fallo en unset*\nNo se encontró un valor para el registro '"+name+"'")


def process_main():
    main = label_table.get('main')
    main.type = REG_TYPE.MAIN
    main.type_defined = True
    global instructions_stack, actual_label
    actual_label = main
    instructions_stack = [] + main.instructions
    process_instructions()


def print_things():
    print("*****************************************")
    print("| ID | LABEL_TYPE |")
    for key in label_table.symbols:
        label = label_table.get(key)
        print("| "+label.name+" | "+label.type.name+" |")
    print("*****************************************")
    print("| ID | SYMBOL_TYPE | VALUE_TYPE | VALUE |")
    print_symbols(symbol_table.symbols)
    print("*****************************************")


def print_symbols(symbols):
    for key in symbols:
        symbol = symbols.get(key)
        if symbol.value_type == TYPE.ARRAY:
            print("| "+symbol.name+" | "+symbol.reg_type.name+" | " +
                  symbol.value_type.name+" | (enlistados abajo) |")
            print_symbols(symbol.value)
        else:
            print("| "+symbol.name+" | "+symbol.reg_type.name+" | " +
                  symbol.value_type.name+" | "+str(symbol.value)+" |")


def parse_ascendent(input):
    try:
        global console_value
        console_value = ''
        labels = AscendentParser.parse(input)
        process_labels(labels)
        process_main()
    except MemoryError:
        print('Se produjo un error en el analisis')
    except RecursionError:
        print('Se produjo un error en el analisis')
    except TypeError:
        print('Se produjo un error en el analisis')
    except InterruptedError:
        print('Ha finalizado la ejecución')
    try:
        print_things()
    except Exception as e:
        print(e)


def parse_descendent(input):
    try:
        global console_value
        console_value = ''
        labels = DescendentParser.parse(input)
        process_labels(labels)
        process_main()
    except MemoryError:
        print('Se produjo un error en el analisis')
    except RecursionError:
        print('Se produjo un error en el analisis')
    except TypeError:
        print('Se produjo un error en el analisis')
    except InterruptedError:
        print('Ha finalizado la ejecución')
    finally:
        try:
            print_things()
        except Exception as e:
            print(e)
