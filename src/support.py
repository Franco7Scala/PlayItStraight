import os
import torch
import time
import numpy
import warnings

from enum import Enum


warnings.filterwarnings("ignore")


model_batch_size = 64
model_learning_rate = 3e-4  # 1e-3
model_momentum = 0.5

# fixed setup code
os.environ["CUDA_VISIBLE_DEVICES"] = "2"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

random_seed = 1

# paths
model_name = "cifar10"
base_path = "/home/scala/projects/DataFiltering/"
dataset_path = base_path + "dataset/{}/"
results_path = base_path + "results"
model_path = "{}/{}.nn".format(results_path, model_name)
model_copy_path = "{}/{}_copy.nn".format(results_path, model_name)
log_path = "{}/log_{}.txt"
reconstruction_image_path = "{}/reconstruction_images_{}.pdf".format(results_path, model_name)
latent_space_distribution_path = "{}/latent_space_distribution_{}.pdf".format(results_path, model_name)

# support variables
_time = 0
_called = False


class Reason(Enum):
    INFO_TRAINING = 2
    SETUP_TRAINING = 3
    LIGHT_INFO_TRAINING = 4
    WARNING = 5
    OUTPUT_TRAINING = 6
    OTHER = 7
    NONE = 8


def get_time_in_millis():
    return int(round(time.time() * 1000))


def clprint(text, reason=Reason.NONE, loggable=False):
    global _called
    global _time
    if not _called:
        _called = True
        _time = get_time_in_millis()

    if reason == Reason.INFO_TRAINING:
        code_color = "\033[94m"

    elif reason == Reason.SETUP_TRAINING:
        code_color = "\033[32m"

    elif reason == Reason.LIGHT_INFO_TRAINING:
        code_color = "\033[92m"

    elif reason == Reason.WARNING:
        code_color = "\033[91m"

    elif reason == Reason.OUTPUT_TRAINING:
        code_color = "\033[95m"

    elif reason == Reason.OTHER:
        code_color = "\033[95m"

    else:
        code_color = "\033[0m"

    if loggable:
        path = log_path.format(results_path, _time)
        file = open(path, "a+")
        file.write(text + "\n")
        file.close()

    print(code_color + str(text) + "\033[0m")


def warm_up():
    clprint("Running on {}...".format(device), Reason.SETUP_TRAINING)
    if not os.path.isdir(results_path):
        os.mkdir(results_path)

    clprint("Current random seed {}!".format(random_seed), Reason.SETUP_TRAINING, loggable=True)
    numpy.random.seed(random_seed)
    torch.manual_seed(random_seed)
    torch.cuda.manual_seed(random_seed)


def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")
