from Evaluator import ExpressionEvaluator


def main():
    context = {
        "weight": 110,
        "height": 193,
        "BMI": 0
    }

    evaluator = ExpressionEvaluator()
    print(evaluator("weight / (height * height)", context))


if __name__ == "__main__":
    main()
