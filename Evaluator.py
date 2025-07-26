import ast
import operator


class ExpressionEvaluator:
    def __init__(self):
        self.allowed_types = {bool, int, float, str}
        self._operators = {
            # binary
            ast.Add: operator.__add__,
            ast.Sub: operator.__sub__,
            ast.Div: operator.__truediv__,
            ast.Mult: operator.__mul__,
            ast.Pow: operator.__pow__,

            # unary
            ast.UAdd: operator.__pos__,
            ast.USub: operator.__neg__,

            # boolean
            ast.And: operator.__and__,
            ast.Or: operator.__or__,

            # bit operations
            ast.BitAnd: operator.__and__,
            ast.BitOr: operator.__or__,
            ast.BitXor: operator.__xor__,

            # comparsion
            ast.Lt: operator.__lt__,
            ast.LtE: operator.__le__,
            ast.Eq: operator.__eq__,
            ast.NotEq: operator.__ne__,
            ast.Gt: operator.__gt__,
            ast.GtE: operator.__ge__,
        }

    def __call__(self, *args, **kwargs):
        expression: str = args[0]
        context: dict = args[1]
        exp = ast.parse(expression, mode="eval").body
        return self.__apply(exp, context)

    def __apply(self, exp: ast.Expression, context: dict):
        if isinstance(exp, ast.Constant):
            value = exp.value
            if type(value) not in self.allowed_types:
                raise SyntaxError(f"Incorrect value: {value!r}")
            return value
        elif isinstance(exp, ast.Name):
            identifier = exp.id
            if identifier not in context:
                raise SyntaxError(f"Variable '{identifier}' not defined!")
            return context[identifier]
        elif isinstance(exp, ast.UnaryOp):
            op = exp.op
            operand = exp.operand
            try:
                return self._operators[type(op)](
                    self.__apply(operand, context))
            except KeyError:
                raise SyntaxError(f"Unknown operation {ast.unparse(exp)}")
        elif isinstance(exp, ast.BinOp):
            op = exp.op
            left = exp.left
            right = exp.right
            try:
                return self._operators[type(op)](
                    self.__apply(left, context),
                    self.__apply(right, context))
            except KeyError:
                raise SyntaxError(f"Unknown operation {ast.unparse(exp)}")
        elif isinstance(exp, ast.Compare):
            ops = exp.ops
            left = exp.left
            comparators = exp.comparators
            # only basic support
            op = ops[0]
            right = comparators[0]
            try:
                return self._operators[type(op)](
                    self.__apply(left, context),
                    self.__apply(right, context))
            except KeyError:
                raise SyntaxError(f"Unknown operation {ast.unparse(exp)}")
        elif isinstance(exp, ast.BoolOp):
            op = exp.op
            values = exp.values
            try:
                return self._operators[type(op)](
                    self.__apply(values[0], context),
                    self.__apply(values[1], context))
            except KeyError:
                raise SyntaxError(f"Unknown operation {ast.unparse(exp)}")
        else:
            raise SyntaxError(f"Unsupported expression: {ast.unparse(exp)}")
