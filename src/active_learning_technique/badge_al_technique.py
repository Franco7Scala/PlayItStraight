import pdb
import numpy
import torch
import torch.nn.functional as functional
import src.support as support

from torch.utils.data.dataloader import DataLoader
from sklearn.utils import stats
from src.active_learning_technique.abstract_al_technique import AbstractALTechnique
from src.al_dataset.dataset import Dataset
from copy import deepcopy


class BadgeALTechnique(AbstractALTechnique):

    def __init__(self, neural_network, dataset):
        self.neural_network = neural_network
        self.dataset = dataset
        self.n_classes = dataset.quantity_classes

    def select_samples(self, unlabeled_samples, labels, n_samples_to_select):
        X_already_labeled, _ = self.dataset.get_train_numpy()
        X_unlabeled_samples = torch.stack(unlabeled_samples)
        X_unlabeled_samples = X_unlabeled_samples.reshape((X_unlabeled_samples.shape[0], X_already_labeled.shape[1])).numpy()
        X = numpy.append(X_already_labeled, X_unlabeled_samples, axis=0)
        grad_embedding = self._get_grad_embedding(X).numpy()
        selected_indexes = self._init_centers(grad_embedding, n_samples_to_select)
        selected_samples = []
        real_outputs = []
        for i in selected_indexes:
            selected_samples.append(unlabeled_samples[i])
            real_outputs.append(labels[i])

        return selected_samples, model_outputs, real_outputs, scores

    def _get_grad_embedding(self, xs):
        emb_dim = self.neural_network.get_embedding_dim()
        self.neural_network.eval()
        n_labels = self.n_classes
        embedding = numpy.zeros([len(xs), n_labels, emb_dim * n_labels])
        loader_te = DataLoader(Dataset(support.input_shape, xs, xs))
        with torch.no_grad():
            for x, y, index in loader_te:
                x = x.to(support.device).type(torch.float32).reshape(self.dataset.shape_data).unsqueeze(0)
                c_out, out = self.neural_network.detailed_forward(x)
                out = out.data.cpu().numpy()
                batch_probs = functional.softmax(c_out, dim=1).data.cpu().numpy()
                max_indexes = numpy.argmax(batch_probs, 1)
                for j in range(len(y)):
                    for c in range(n_labels):
                        if c == max_indexes[j]:
                            embedding[index[j]][emb_dim * c: emb_dim * (c + 1)] = deepcopy(out[j]) * (1 - batch_probs[j][c])

                        else:
                            embedding[index[j]][emb_dim * c: emb_dim * (c + 1)] = deepcopy(out[j]) * (-1 * batch_probs[j][c])

            return torch.Tensor(embedding)

    def _init_centers(self, X, K):
        embs = torch.Tensor(X).to(support.device)
        ind = torch.argmax(torch.norm(embs, 2, 1)).item()
        mu = [embs[ind]]
        inds_all = [ind]
        cent_inds = [0.] * len(embs)
        cent = 0
        while len(mu) < K:
            if len(mu) == 1:
                D2 = torch.cdist(mu[-1].view(1, -1), embs, 2)[0].cpu().numpy()
            else:
                new_d = torch.cdist(mu[-1].view(1, -1), embs, 2)[0].cpu().numpy()
                for i in range(len(embs)):
                    if D2[i] > new_d[i]:
                        cent_inds[i] = cent
                        D2[i] = new_d[i]

            if sum(D2) == 0.0:
                pdb.set_trace()

            D2 = D2.ravel().astype(float)
            d_dist = (D2 ** 2) / sum(D2 ** 2)
            custom_dist = stats.rv_discrete(name="custm", values=(numpy.arange(len(D2)), d_dist))
            ind = custom_dist.rvs(size=1)[0]
            while ind in inds_all:
                ind = custom_dist.rvs(size=1)[0]

            mu.append(embs[ind])
            inds_all.append(ind)
            cent += 1

        return inds_all