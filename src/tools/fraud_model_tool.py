from src.models.train import FraudModel


class FraudModelTool:
    def __init__(self, settings):
        self.model = FraudModel(settings.artifacts)

    def predict(self, transaction):
        return self.model.score(transaction)
