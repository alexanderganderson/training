"""Training and validation code for bddmodelcar."""
import sys
import traceback
import logging

from Parameters import ARGS
from Dataset import Dataset
import Utils

import matplotlib.pyplot as plt

from nets.SqueezeNet import SqueezeNet
from torch.autograd import Variable
import torch.nn.utils as nnutils
import torch


def main():
    logging.basicConfig(filename='training.log', level=logging.DEBUG)
    logging.debug(ARGS)  # Log arguments

    # Set Up PyTorch Environment
    # torch.set_default_tensor_type('torch.FloatTensor')
    torch.cuda.set_device(ARGS.gpu)
    torch.cuda.device(ARGS.gpu)

    net = SqueezeNet().cuda()
    criterion = torch.nn.MSELoss().cuda()
    optimizer = torch.optim.Adadelta(net.parameters())

    try:
        epoch = ARGS.epoch

        if not epoch == 0:
            import os
            print("Resuming")
            save_data = torch.load(os.path.join(ARGS.save_path, "epoch%02d.weights" % (epoch - 1,)))
            net.load_state_dict(save_data)

        logging.debug('Starting training epoch #{}'.format(epoch))

        net.train()  # Train mode

        train_dataset = Dataset('/hostroot/data/dataset/bair_car_data_Main_Dataset', ['furtive'], [])
        train_data_loader = torch.utils.data.DataLoader(train_dataset,
                                                        batch_size=500,
                                                        shuffle=False, pin_memory=False)

        train_loss = Utils.LossLog()

        for camera, meta, truth, mask in train_data_loader:
            # Forward
            optimizer.zero_grad()
            outputs = net(Variable(camera.cuda()), Variable(meta.cuda())).cuda()
            loss = criterion(outputs, Variable(target_data.cuda()))

            # Backpropagate
            loss.backward()
            nnutils.clip_grad_norm(net.parameters(), 1.0)
            optimizer.step()

            # Logging Loss
            train_loss.add(batch.loss.data[0])

        Utils.csvwrite('trainloss.csv', [train_loss.average()])

        logging.debug('Finished training epoch #{}'.format(epoch))
        logging.debug('Starting validation epoch #{}'.format(epoch))

        val_dataset = Dataset('/hostroot/data/dataset/bair_car_data_Main_Dataset', ['direct'], [])
        val_data_loader = torch.utils.data.DataLoader(train_dataset,
                                                        batch_size=500,
                                                        shuffle=False, pin_memory=False)

        val_loss = Utils.LossLog()

        for camera, meta, truth, mask in val_data_loader:
            # Forward
            optimizer.zero_grad()
            outputs = net(Variable(camera.cuda()), Variable(meta.cuda())).cuda()
            loss = criterion(outputs, Variable(target_data.cuda()))

            # Logging Loss
            val_loss.add(batch.loss.data[0])

        Utils.csvwrite('valloss.csv', [val_loss.average()])

        logging.debug('Finished validation epoch #{}'.format(epoch))
        Utils.save_net("epoch%02d" % (epoch,), net)

    except Exception:
        logging.error(traceback.format_exc())  # Log exception
        sys.exit(1)

if __name__ == '__main__':
    main()
