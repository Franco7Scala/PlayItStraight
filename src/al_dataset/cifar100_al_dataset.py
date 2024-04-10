import src.support as support
from src.al_dataset.abstract_al_dataset import AbstractALDataset
from torchvision import datasets, transforms


class Cifar100ALDataset(AbstractALDataset):

    def __init__(self, quantity_samples):
        test_dataset = datasets.CIFAR100(root=support.dataset_path.format("cifar100"), train=False, transform=transforms.ToTensor(), download=True)
        train_dataset = datasets.CIFAR100(root=support.dataset_path.format("cifar100"), train=True, transform=transforms.ToTensor(), download=True)
        super(Cifar100ALDataset, self).__init__(quantity_samples, test_dataset, train_dataset, (3, 32, 32))
