import torch
import torch.nn as nn
from scipy import stats
import numpy as np
import models
import data_loader
import torch_optimizer as optim
from lion_pytorch import Lion

# should wrap in nn.DataParallel if multiGPU
# here I opted for two seperate runs for more hyperparameter experimentation
torch.cuda.set_device(0)

class HyperIQASolver(object):
    """Solver for training and testing hyperIQA"""
    def __init__(self, config, path, train_idx, test_idx):

        self.epochs = config.epochs
        self.test_patch_num = config.test_patch_num

        self.model_hyper = models.HyperNet(16, 112, 224, 112, 56, 28, 14, 7).cuda()
        self.model_hyper.train(True)

        self.loss_fn = torch.nn.L1Loss().cuda()

        backbone_params = list(map(id, self.model_hyper.res.parameters()))
        self.hypernet_params = filter(lambda p: id(p) not in backbone_params, self.model_hyper.parameters())
        self.lr = config.lr
        self.lrratio = config.lr_ratio
        self.weight_decay = config.weight_decay
        paras = [{'params': self.hypernet_params, 'lr': self.lr * self.lrratio}, {'params': self.model_hyper.res.parameters(), 'lr': self.lr}]
        self.solver = torch.optim.Adam(paras, weight_decay=self.weight_decay)
        # self.solver = Lion(paras, weight_decay=self.weight_decay) #, betas=(0.95, 0.98))
        # self.solver = optim.Adafactor(paras, weight_decay=self.weight_decay)

        train_loader = data_loader.DataLoader(config.dataset, path, train_idx, config.patch_size, config.train_patch_num, batch_size=config.batch_size, istrain=True)
        test_loader = data_loader.DataLoader(config.dataset, path, test_idx, config.patch_size, config.test_patch_num, istrain=False)
        self.train_data = train_loader.get_data()
        self.test_data = test_loader.get_data()

    def train(self):
        # for resuming training
        # self.model_hyper.load_state_dict(torch.load( "hyperIQA_hybrid.pth"))
        """Training"""
        best_srcc = 0.0
        best_plcc = 0.0
        print('Epoch\tTrain_Loss\tTrain_SRCC\tTest_SRCC\tTest_PLCC')
        for t in range(self.epochs):
            epoch_loss = []
            pred_scores = []
            gt_scores = []

            for img, label in self.train_data:
                img = img.cuda().clone().detach()
                label = label.cuda().clone().detach()

                self.solver.zero_grad()

                # Generate weights for target network
                paras = self.model_hyper(img)  # 'paras' contains the network weights conveyed to target network

                # Building target network
                model_target = models.TargetNet(paras).cuda()
                for param in model_target.parameters():
                    param.requires_grad = False

                # Quality prediction
                pred = model_target(paras['target_in_vec'])  # while 'paras['target_in_vec']' is the input to target net
                pred_scores = pred_scores + pred.cpu().tolist()
                gt_scores = gt_scores + label.cpu().tolist()

                loss = self.loss_fn(pred.squeeze(), label.float().detach())
                epoch_loss.append(loss.item())
                loss.backward()
                self.solver.step()

            train_srcc, _ = stats.spearmanr(pred_scores, gt_scores)

            test_srcc, test_plcc = self.test(self.test_data)
            torch.save(self.model_hyper.state_dict(), f"hyperIQA_hybrid_{t+1}.pth")
            if test_srcc > best_srcc:
                best_srcc = test_srcc
                torch.save(self.model_hyper.state_dict(), "hyperIQA_hybrid_srcc.pth")
            if test_plcc > best_plcc:
                best_plcc = test_plcc
                torch.save(self.model_hyper.state_dict(), "hyperIQA_hybrid_plcc.pth")
            print('%d\t%4.3f\t\t%4.4f\t\t%4.4f\t\t%4.4f' %
                  (t + 1, sum(epoch_loss) / len(epoch_loss), train_srcc, test_srcc, test_plcc))

            # Update optimizer
            lr = self.lr / pow(10, (t // 6))
            if t > 8:
                self.lrratio = 1
            self.solver.param_groups[0]["lr"] = lr * self.lrratio

        print('Best test SRCC %f, PLCC %f' % (best_srcc, best_plcc))

        return best_srcc, best_plcc

    def test(self, data):
        """Testing"""
        self.model_hyper.train(False)
        pred_scores = []
        gt_scores = []

        for img, label in data:
            # Data.
            img = img.cuda().clone().detach()
            label = label.cuda().clone().detach()

            paras = self.model_hyper(img)
            model_target = models.TargetNet(paras).cuda()
            model_target.train(False)
            pred = model_target(paras['target_in_vec'])

            pred_scores.append(float(pred.item()))
            gt_scores = gt_scores + label.cpu().tolist()

        pred_scores = np.mean(np.reshape(np.array(pred_scores), (-1, self.test_patch_num)), axis=1)
        gt_scores = np.mean(np.reshape(np.array(gt_scores), (-1, self.test_patch_num)), axis=1)
        test_srcc, _ = stats.spearmanr(pred_scores, gt_scores)
        test_plcc, _ = stats.pearsonr(pred_scores, gt_scores)

        self.model_hyper.train(True)
        return test_srcc, test_plcc
