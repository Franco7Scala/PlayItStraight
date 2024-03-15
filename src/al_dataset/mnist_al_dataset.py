import src.support as support
from src.al_dataset.abstract_al_dataset import AbstractALDataset
from torchvision import datasets, transforms


class MNISTALDataset(AbstractALDataset):

    def __init__(self, quantity_samples):
        test_dataset = datasets.MNIST(root=support.dataset_path.format("mnist"), train=False, transform=transforms.ToTensor(), download=True)
        train_dataset = datasets.MNIST(root=support.dataset_path.format("mnist"), train=True, transform=transforms.ToTensor(), download=True)
        super(MNISTALDataset, self).__init__(quantity_samples, test_dataset, train_dataset, (28, 28))
