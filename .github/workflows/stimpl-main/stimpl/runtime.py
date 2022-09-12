from typing import Any, Tuple, Optional

from stimpl.expression import *
from stimpl.types import *
from stimpl.errors import *

"""
Interpreter State
"""


class State(object):
    def __init__(self, variable_name: str, variable_value: Expr, variable_type: Type, next_state: 'State') -> None:
        self.variable_name = variable_name
        self.value = (variable_value, variable_type)
        self.next_state = next_state

    def copy(self) -> 'State':
        variable_value, variable_type = self.value
        return State(self.variable_name, variable_value, variable_type, self.next_state)

    def set_value(self, variable_name, variable_value, variable_type):
        return State(variable_name, variable_value, variable_type, self)

    def get_value(self, variable_name) -> Any:                                           # Function to get value
        if self.variable_name == variable_name:
            return self.value
        return self.next_state.get_value(variable_name)

    def __repr__(self) -> str:
        return f"{self.variable_name}: {self.value}, " + repr(self.next_state)


class EmptyState(State):
    def __init__(self):
        pass

    def copy(self) -> 'EmptyState':
        return EmptyState()

    def get_value(self, variable_name) -> None:
        return None

    def __repr__(self) -> str:
        return ""


"""
Main evaluation logic!
"""


def evaluate(expression: Expr, state: State) -> Tuple[Optional[Any], Type, State]:
    match expression:
        case Ren():
            return (None, Unit(), state)

        case IntLiteral(literal=l):
            return (l, Integer(), state)

        case FloatingPointLiteral(literal=l):
            return (l, FloatingPoint(), state)

        case StringLiteral(literal=l):
            return (l, String(), state)

        case BooleanLiteral(literal=l):
            return (l, Boolean(), state)

        case Print(to_print=to_print):
            printable_value, printable_type, new_state = evaluate(
                to_print, state)

            match printable_type:
                case Unit():
                    print("Unit")
                case _:
                    print(f"{printable_value}")

            return (printable_value, printable_type, new_state)

        case Sequence(exprs=exprs) | Program(exprs=exprs):                         # This case takes a sequence of conditions and does them
            for expr in exprs:
                value, expr_type, state = evaluate(expr, state)
            return(value, expr_type, state)

        case Variable(variable_name=variable_name):
            value = state.get_value(variable_name)
            if value == None:
                raise InterpSyntaxError(
                    f"Cannot read from {variable_name} before assignment.")
            variable_value, variable_type = value
            return (variable_value, variable_type, state)

        case Assign(variable=variable, value=value):

            value_result, value_type, new_state = evaluate(value, state)

            variable_from_state = new_state.get_value(variable.variable_name)
            _, variable_type = variable_from_state if variable_from_state else (
                None, None)

            if value_type != variable_type and variable_type != None:
                raise InterpTypeError(f"""Mismatched types for Assignment:
            Cannot assign {value_type} to {variable_type}""")

            new_state = new_state.set_value(
                variable.variable_name, value_result, value_type)
            return (value_result, value_type, new_state)

        case Add(left=left, right=right):
            result = 0
            left_result, left_type, new_state   = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Add:
            Cannot add {left_type} to {right_type}""")

            match left_type:
                case Integer() | String() | FloatingPoint():
                    result = left_result + right_result
                case _:
                    raise InterpTypeError(f"""Cannot add {left_type}s""")

            return (result, left_type, new_state)

        case Subtract(left=left, right=right):                                     # This case handles subtraction of two params
            result = 0
            left_result, left_type, new_state = evaluate(left, state)              # Gets result, type and new state for left 
            right_result, right_type, new_state = evaluate(right, new_state)       # Gets result, type and new state for right

            if left_type != right_type:                                            # A check to make sure left and right have the same type
                raise InterpTypeError(f"""Mismatched types for Subtract:           
            Cannot subtract {left_type} to {right_type}""")                        # Raises InterpTypeError if types are different

            match left_type:
                case Integer() | FloatingPoint():                                  # If type is int or float, subtraction as usual
                    result = left_result - right_result
                case _:
                    raise InterpTypeError(f"""Cannot subtract {left_type}s""")     # Otherwise InterpTypeError is raised

            return (result, left_type, new_state)                                  # Returns the result, the types, and the new state

        case Multiply(left=left, right=right):                                     # Same as Subtract case, but for multiplication
            result = 0
            left_result, left_type, new_state = evaluate(left, state)
            right_result, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Multiply:
            Cannot multiply {left_type} to {right_type}""")

            match left_type:
                case Integer() | FloatingPoint():
                    result = left_result * right_result
                case _:
                    raise InterpTypeError(f"""Cannot multiply {left_type}s""")

            return (result, left_type, new_state)

        case Divide(left=left, right=right):                                       # Pretty much the same as subtraction but also includes a check
            left_result, left_type, new_state   = evaluate(left, state)            # to make sure you aren't dividing by zero
            right_result, right_type, new_state = evaluate(right, new_state)
            
            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Divide:
            Cannot divide {left_type} to {right_type}""")
            if right_result == 0 or right_result == 0.0:
                raise InterpMathError

            match left_type:
                case Integer():
                    if right_result != 0 or right_result != 0.0:
                        result = left_result / right_result
                        result = int(result)                                      # This returns an int if the types are int
                case FloatingPoint():
                    if right_result != 0 or right_result != 0.0:
                        result = left_result / right_result
                case _:
                    raise InterpTypeError(f"""Cannot divide {left_type}s""")

            return (result, left_type, new_state)

        case And(left=left, right=right):                                          # Part of Skeleton Code 
            left_value, left_type, new_state   = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for And:
            Cannot add {left_type} to {right_type}""")
            match left_type:
                case Boolean():
                    result = left_value and right_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical and on non-boolean operands.")

            return (result, left_type, new_state)

        case Or(left=left, right=right):                                           # Case for the use of the OR operator                   
            left_value, left_type, new_state   = evaluate(left, state)             # on left and right
            right_value, right_type, new_state = evaluate(right, new_state)        # Updates the state for both left and right

            if left_type != right_type:                                            # Makes sure types are the same, otherwise raise error
                raise InterpTypeError(f"""Mismatched types for Or:
            Cannot compare {left_type} to {right_type}""")
            match left_type:
                case Boolean():                                                    # Boolean is awesome because you do the OR operator here
                    result = left_value or right_value
                case _:                                                            # Otherwise, ERROR
                    raise InterpTypeError(
                        "Cannot perform logical or on non-boolean operands.")
            return (result, left_type, new_state)                                  # Returns result, type, and new state

        case Not(expr=expr):                                                       # Literally the exact same as the OR case, except on the NOT operator
            expr_value, expr_type, new_state = evaluate(expr, state)
            match expr_type:
                case Boolean():
                    result = not expr_value
                case _:
                    raise InterpTypeError(
                        "Cannot perform logical not on non-boolean operand.")
            return(result, expr_type, new_state)
            
        case If(condition=condition, true=true, false=false):                      # Case for using If statement
            condition_value, condition_type, new_state = evaluate(condition, state)   # Take the condition and update the state

            result = None

            match condition_type:
                case Boolean():                                                       # Boolean case
                    if condition_value:                                               # if true, evaluate true and return the result, true type, and new state
                        true_value, true_type, new_state = evaluate(true, new_state)
                        result = true_value
                        return(result, true_type, new_state)
                    else:                                                             # if false, evaluate false and return the result, false type, and new state
                        false_value, false_type, new_state = evaluate(false, new_state)
                        result = false_value
                        return(result, false_type, new_state)
                case _:                                                               # If it's not a boolean, raise an error
                    raise InterpTypeError(f"""Invalid type for if condition: 
                Cannot use {condition_type}""")

        case Lt(left=left, right=right):
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Lt:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value < right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform < on {left_type} type.")

            return (result, Boolean(), new_state)

        case Lte(left=left, right=right):                                          # Case for Less than or equal to operator
            left_value, left_type, new_state = evaluate(left, state)               # Get the values, types, and update the state for left and right
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:                                            # Check to make sure types are the same
                raise InterpTypeError(f"""Mismatched types for Lte:
            Cannot compare {left_type} to {right_type}""")
            
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():           # Do the Operation!
                    result = left_value <= right_value
                case Unit():                                                       # Unit Returns True
                    result = True                                            
                case _:                                                            # Anything else, raise an error :(
                    raise InterpTypeError(
                        f"Cannot perform <= on {left_type} type.")
            
            return (result, Boolean(), new_state)                                 # Return everything!

        case Gt(left=left, right=right):                                          # Same as Lte but for greater than operator
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gt:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value > right_value
                case Unit():                                                    # Unit returns false
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform > on {left_type} type.")
            
            return (result, Boolean(), new_state)

        case Gte(left=left, right=right):                                         # Same as Lte but for Gte
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Gte:
            Cannot compare {left_type} to {right_type}""")
            
            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value >= right_value
                case Unit():
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform >= on {left_type} type.")
            
            return (result, Boolean(), new_state)

        case Eq(left=left, right=right):                                          # Same as Lte but checks equivalence
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Eq:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value == right_value
                case Unit():
                    result = True
                case _:
                    raise InterpTypeError(
                        f"Cannot perform == on {left_type} type.")
                
            return (result, Boolean(), new_state)

        case Ne(left=left, right=right):                                          # The same as Eq but checks if l and r are NOT equal 
            left_value, left_type, new_state = evaluate(left, state)
            right_value, right_type, new_state = evaluate(right, new_state)

            result = None

            if left_type != right_type:
                raise InterpTypeError(f"""Mismatched types for Ne:
            Cannot compare {left_type} to {right_type}""")

            match left_type:
                case Integer() | Boolean() | String() | FloatingPoint():
                    result = left_value != right_value
                case Unit():
                    result = False
                case _:
                    raise InterpTypeError(
                        f"Cannot perform != on {left_type} type.")
                
            return (result, Boolean(), new_state)

        case While(condition=condition, body=body):                               # While loop case
            condition_value, condition_type, new_state = evaluate(condition, state) # This one was fun!!

            match condition_type:
                case Boolean():                                                    # If the type is Boolean, YAY, otherwise raise an error
                    pass
                case _:
                    raise InterpTypeError(f"""Invalid type for while condition: 
                                                Cannot use {condition_type}""")
            while condition_value:                                                 # Each iteration of this loop checks the bodys value and type and updates the state
                body_value, body_type, new_state = evaluate(body, new_state)       # Also does the same for the condition value and type and updating the state
                condition_value, condition_type, new_state = evaluate(condition, new_state)
            return(False, condition_type, new_state)                               # While loops always return false

        case _:
            raise InterpSyntaxError("Unhandled!")
    pass


def run_stimpl(program, debug=False):
    state = EmptyState()
    program_value, program_type, program_state = evaluate(program, state)

    if debug:
        print(f"program: {program}")
        print(f"final_value: ({program_value}, {program_type})")
        print(f"final_state: {program_state}")

    return program_value, program_type, program_state
