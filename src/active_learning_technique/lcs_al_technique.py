import numpy
import torch
import heapq
import src.support as support

from src.active_learning_technique.abstract_al_technique import AbstractALTechnique


class LCSALTechnique(AbstractALTechnique):

    def __init__(self, neural_network):
        self.neural_network = neural_network

    def select_samples(self, x, y, n_samples_to_select):
        selected_samples = []
        confidences = []
        model_outputs = []
        real_outputs = []

        for i in range(len(x)):
            # calculating least confidence
            out_model = self.neural_network(torch.unsqueeze(x[i], 0).to(support.device))[0]
            #out_model = self.neural_network(sample.to(support.device))[0]
            simple_least_confidence = numpy.nanmax(out_model.cpu().detach().numpy())
            normalized_least_confidence = (1 - simple_least_confidence) * (len(out_model) / (len(out_model) - 1)).detach().numpy()
            # appending
            if len(selected_samples) >= n_samples_to_select:
                min_confidence = min(confidences)
                min_confidence_index = confidences.index(min_confidence)
                if normalized_least_confidence > min_confidence:
                    selected_samples.pop(min_confidence_index)
                    confidences.pop(min_confidence_index)
                    model_outputs.pop(min_confidence_index)
                    real_outputs.pop(min_confidence_index)
                    selected_samples.append(x[i])
                    confidences.append(normalized_least_confidence)
                    model_outputs.append(out_model)
                    real_outputs.append(y[i])

            else:
                selected_samples.append(x[i])
                confidences.append(normalized_least_confidence)
                model_outputs.append(out_model)
                real_outputs.append(y[i])

        return selected_samples, model_outputs, real_outputs, confidences
