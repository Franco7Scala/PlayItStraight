'''
import numpy
import torch
from torch import nn

from src import support
from src.neural_networks import fashion_mnist_vae
from src.neural_networks.fashion_mnist_vae import Fashion_MNIST_VAE
from src.support import clprint, Reason, get_time_in_millis


class SimpleActiveLearner:

    def __init__(self, dataset, al_technique, early_stopping_threshold):
        self.dataset = dataset
        self.al_technique = al_technique
        self.n_samples_to_select = -1
        self.early_stopping_threshold = early_stopping_threshold

    def elaborate(self, model, al_epochs, training_epochs, n_samples_to_select, criterion, optimizer):
        self.n_samples_to_select = n_samples_to_select
        clprint("Starting Active Learning process...", Reason.INFO_TRAINING)
        self._train_model(criterion, model, optimizer, training_epochs)
        for i in range(al_epochs):
            clprint("Making n.{}/{} AL epochs...".format(i + 1, al_epochs), Reason.INFO_TRAINING, loggable=True)
            clprint("Selecting {} new samples...".format(self.n_samples_to_select), Reason.INFO_TRAINING)
            start_time = get_time_in_millis()
            self._select_next_samples(self.n_samples_to_select, al_epochs)
            end_time = get_time_in_millis()
            clprint("Elapsed time: {}".format(end_time - start_time), Reason.LIGHT_INFO_TRAINING, loggable=True)
            self._train_model(criterion, model, optimizer, training_epochs)

    def _train_model(self, criterion, model, optimizer, training_epochs):
        clprint("Training model...", Reason.INFO_TRAINING)
        model.fit(training_epochs, criterion, optimizer, self.dataset.get_train_loader())
        clprint("Evaluating model...", Reason.INFO_TRAINING)
        loss, accuracy = model.evaluate(criterion, self.dataset.get_test_loader())
        clprint("Loss: {}\nAccuracy: {}".format(loss, accuracy), Reason.LIGHT_INFO_TRAINING, loggable=True)

    def _select_next_samples(self, n_samples_to_select, al_epochs):
        x, y = self.dataset.get_unselected_data()
        selected_x, model_y, selected_y, t_scores = self.al_technique.select_samples(x, y, n_samples_to_select)
        quantity_classes = max(y) + 1
        # lavorare su:
        # - selezionare meno dati da utilizzare come pool (magari prendendone n fissati per ogni classe e poi far variare la selezione in base alle classi più incerte)
        # - combinare piu tecniche di AL e magari pesarle
        # - vedere come impostare la query size (magari anche rendendola dinamica)
        # - CL?
        # - Andiamo meglio di distillation?

        scores = []
        for i in range(len(selected_x)):
            # ATTEMPT 1 alone
            #diff = torch.linalg.norm(torch.tensor(numpy.eye(quantity_classes)[y[i]]).to(support.device) - model_y[i].to(support.device))
            #scores.append(diff.item())

            # ATTEMPT 1
            diff = torch.linalg.norm(torch.tensor(numpy.eye(quantity_classes)[y[i]]).to(support.device) - model_y[i].to(support.device))
            scores.append(t_scores[i].item() + diff.item())

            # ATTEMPT 2
            # current_output = model_y[i]
            # max_val = torch.max(torch.cat([current_output[0:y[i]], current_output[y[i]+1:]]))
            # diff = current_output[y[i]] - max_val
            # scores.append(t_scores[i].item() - diff)

            # ATTEMPT 3
            # current_output = model_y[i]
            # diff = current_output[y[i]]
            # scores.append(diff + t_scores[i].item())

            # ATTEMPT 4
            # current_output = model_y[i]
            # diff = 1 - current_output[y[i]]
            # scores.append(diff + t_scores[i].item())

            # ATTEMPT 5.1 e 5.2
            #loss = nn.CrossEntropyLoss()
            #diff = loss(torch.tensor(numpy.eye(quantity_classes)[y[i]]).to(support.device), model_y[i].to(support.device))
            #diff = torch.nn.functional.kl_div(torch.tensor(numpy.eye(quantity_classes)[y[i]]).to(support.device), model_y[i].to(support.device), reduction='mean')
            #scores.append(t_scores[i].item() + diff.item())


        def sort_by_float(current_tuple):
            return current_tuple[0]

        combined_list = list(zip(scores, selected_x))
        combined_list = sorted(combined_list, key=sort_by_float, reverse=True)
        scores, selected_xP = zip(*combined_list)

        # additive balancing
        # counters_for_classes = [0] * quantity_classes
        # balanced_x = []
        # for i in range(len(selected_x)):
        #     if i < len(selected_x) / 2:
        #         current_class = y[i]
        #         counters_for_classes[current_class] += 1
        #         balanced_x.append(x[i])
        #         if i == (len(selected_x) / 2) - 1:
        #             n_samples_to_select_for_each_class = max(counters_for_classes)  # da mettere in un posto migliore
        #
        #     else:
        #         current_class = y[i]
        #         if counters_for_classes[current_class] < n_samples_to_select_for_each_class:
        #             counters_for_classes[current_class] += 1
        #             balanced_x.append(x[i])
        #
        # print(len(balanced_x))
        # self.dataset.annotate(balanced_x)



        # balancing
        # n_samples_to_select_for_each_class = int(n_samples_to_select/quantity_classes)
        # counters_for_classes = [0] * quantity_classes
        # balanced_x = []
        # for i in range(len(x)):
        #     current_class = y[i]
        #     if counters_for_classes[current_class] < n_samples_to_select_for_each_class:
        #         counters_for_classes[current_class] += 1
        #         balanced_x.append(x[i])
        #
        # self.dataset.annotate(balanced_x)

        # CL
        if al_epochs <= 10:
            quantity_to_take = n_samples_to_select - (((n_samples_to_select/10)/2) * (10 - al_epochs))
            goodness = []
            for i in range(len(selected_x)):
                loss = torch.nn.CrossEntropyLoss()
                goodness.append(loss(model_y, selected_y))

            c_list = list(zip(goodness, selected_x))
            c_list = sorted(c_list, key=sort_by_float, reverse=False)
            goodness, selected_x = zip(*c_list)

            self.dataset.annotate(selected_x[:quantity_to_take])
            self.dataset.annotate(selected_xP[:n_samples_to_select - quantity_to_take])

        else:
            self.dataset.annotate(selected_xP[:n_samples_to_select])


        # vae = Fashion_MNIST_VAE(support.vae_dim_code, support.device)
        # vae = fashion_mnist_vae.load_model(support.vae_dim_code, "../../results/fashion_mnist_vae.nn", support.device)
        # vae.eval()
        # distilled_data = []
        #
        # for instance in selected_xP[:n_samples_to_select]:
        #     xx = instance.to(support.device).unsqueeze(0)
        #     _, _, res = vae(xx)
        #     distilled_data.append(res.squeeze(0).to(support.device))
        #
        # self.dataset.annotate_and_replace(selected_xP[:n_samples_to_select], distilled_data)

        #self.dataset.annotate(selected_xP[:n_samples_to_select])
        clprint("Updating AL technique...".format(self.n_samples_to_select), Reason.LIGHT_INFO_TRAINING)
        self.al_technique.update(self.dataset)










def plain_training(model, plain_training_epochs, incremental_training_epochs, criterion, optimizer, n_samples_at_start, dataset):
    clprint("Loading dataset...", Reason.INFO_TRAINING)
    clprint("Starting training with all samples!".format(n_samples_at_start), Reason.INFO_TRAINING, loggable=True)
    clprint("Plain training model...", Reason.INFO_TRAINING)
    for i in range(incremental_training_steps):
        start_time = support.get_time_in_millis()
        model.fit(incremental_training_epochs, criterion, optimizer, dataset.get_train_loader())
        elapsed_time = support.get_time_in_millis() - start_time
        clprint("Evaluating model...", Reason.INFO_TRAINING)
        loss, accuracy = model.evaluate(criterion, dataset.get_test_loader())
        if i == incremental_training_steps - 1:
            reason = Reason.OTHER

        else:
            reason = Reason.LIGHT_INFO_TRAINING

        clprint("Loss: {}\nAccuracy: {}\nReached in {} seconds".format(loss, accuracy, int(elapsed_time / 1000)), reason, loggable=True)

'''