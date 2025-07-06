from Evaluator import ExpressionEvaluator


def main():
    context = {
        "weight": 110
    }

    evaluator = ExpressionEvaluator()
    print(evaluator("(weight <= 100) * 5", context))


if __name__ == "__main__":
    main()
