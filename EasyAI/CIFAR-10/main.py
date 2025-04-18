import os
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision
import torchvision.transforms as transforms
import matplotlib.pyplot as plt
import numpy as np
from torch.utils.data import DataLoader
from tqdm import tqdm

script_dir = os.path.dirname(os.path.abspath(__file__))
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"使用设备: {device}")


# 1. 数据预处理与加载

# 定义数据变换：CIFAR-10图像为3通道彩色图像，需要归一化处理
transform_train = transforms.Compose([
    transforms.RandomCrop(32, padding=4),  # 随机裁剪，数据增强
    transforms.RandomHorizontalFlip(),  # 随机水平翻转，数据增强
    transforms.ToTensor(),  # 转换为Tensor
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))  # RGB三通道归一化
])
transform_test = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize((0.4914, 0.4822, 0.4465), (0.2023, 0.1994, 0.2010))
])

# 下载并加载CIFAR-10训练集和测试集
train_dataset = torchvision.datasets.CIFAR10(
    root=os.path.join(script_dir, 'data'),
    train=True,
    download=True,
    transform=transform_train
)

test_dataset = torchvision.datasets.CIFAR10(
    root=os.path.join(script_dir, 'data'),
    train=False,
    download=True,
    transform=transform_test
)

# 创建数据加载器
batch_size = 128  # 批量大小
train_loader = DataLoader(
    train_dataset,
    batch_size=batch_size,
    shuffle=True,
    num_workers=0  # 多进程加载数据
)
test_loader = DataLoader(
    test_dataset, 
    batch_size=batch_size,
    shuffle=False,
    num_workers=0
)

# CIFAR-10类别名称
classes = ('plane', 'car', 'bird', 'cat', 'deer', 
           'dog', 'frog', 'horse', 'ship', 'truck')

# 打印数据集信息
print(f"训练集大小: {len(train_dataset)}")
print(f"测试集大小: {len(test_dataset)}")
print(f"图像大小: {train_dataset[0][0].shape}")  # [3, 32, 32] - [通道数, 高度, 宽度]
print(f"类别: {classes}")


# 2. 可视化一些训练图像
def imshow(img):
    '''显示图像函数，用于可视化数据集样本'''
    # 反归一化：将归一化的张量转回原始图像
    img = img / 2 + 0.5
    npimg = img.numpy()
    # 转换通道顺序从(C,H,W)到(H,W,C)
    plt.imshow(np.transpose(npimg, (1, 2, 0)))
    plt.axis('off')


def visualize_samples(train_loader):
    '''可视化训练样本'''
    # 获取一些训练图像
    dataiter = iter(train_loader)
    images, labels = next(dataiter)

    # 创建图像网络
    plt.figure(figsize=(10, 4))
    # 显示一批图像
    imshow(torchvision.utils.make_grid(images[:8]))
    # 打印对应标签
    print(' '.join(f'{classes[labels[j]]}' for j in range(8)))

    plt.show()


# 3. 定义卷积神经网络模型

class CIFAR10CNN(nn.Module):
    """
    卷积神经网络模型 - 用于CIFAR-10图像分类
    - 3个卷积层 每层后接最大池化和ReLU激活
    - 2个全连接层
    - 使用批归一化加速训练和提高性能
    - Dropout防止过拟合
    """
    def __init__(self):
        super().__init__()

        # 第一个卷积块
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)  # 输入3通道，输出32通道，3x3卷积核
        self.bn1 = nn.BatchNorm2d(32)  # 批归一化: 加速收敛，提供正则化效果

        # 第二个卷积块
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(64)

        # 第三个卷积块
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, padding=1)
        self.bn3 = nn.BatchNorm2d(128)

        # 池化层(用于所有卷积块)
        self.pool = nn.MaxPool2d(2, 2)  # 2x2最大池化，步长为2

        # 计算全连接层的输入特征数
        # 32x32图像经过3次池化变为4x4，通道数为128
        fc_input_size = 128 * 4 * 4

        # 全连接层
        self.fc1 = nn.Linear(fc_input_size, 512)  # 128*4*4 -> 512
        self.dropout = nn.Dropout(0.5)  # Dropout防止过拟合
        self.fc2 = nn.Linear(512, 10)  # 512 -> 10 个类别

    def forward(self, x):
        '''前向传播'''
        # 第一个卷积块: 卷积 -> 批归一化 -> ReLu -> 池化
        x = self.pool(torch.relu(self.bn1(self.conv1(x))))

        # 第二个卷积块: 卷积 -> 批归一化 -> ReLu -> 池化
        x = self.pool(torch.relu(self.bn2(self.conv2(x))))

        # 第三个卷积块: 卷积 -> 批归一化 -> ReLu -> 池化
        x = self.pool(torch.relu(self.bn3(self.conv3(x))))

        # 展平操作，将4D张量转为2D
        x = x.view(x.size(0), -1)

        # 全连接层，使用ReLu和Dropout
        x = torch.relu(self.fc1(x))
        x = self.dropout(x)

        # 输出层(不使用激活函数，因为稍后会用交叉熵损失)
        x = self.fc2(x)
        return x
    
# 创建模型实例
model = CIFAR10CNN().to(device)
print(model)



# 4. 定义损失函数和优化器

# 交叉熵损失，适用于多分类问题
criterion = nn.CrossEntropyLoss()

# 使用SGD优化器，学习率为0.01
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9, weight_decay=5e-4)

# 学习率调度器：每7个epoch将学习率乘以0.1
scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=7, gamma=0.1)


# 5. 训练模型

def train(num_epochs):
    '''训练模型'''
    print('开始训练...')

    for epoch in range(num_epochs):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for inputs, labels in tqdm(train_loader):
            inputs, labels = inputs.to(device), labels.to(device)

            # 梯度清零
            optimizer.zero_grad()

            # 前向传播
            outputs = model(inputs)

            # 计算损失
            loss = criterion(outputs, labels)

            # 反向传播计算梯度
            loss.backward()

            # 更新权重
            optimizer.step()

            # 统计损失
            running_loss += loss.item()

            # 统计准确率
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()


        print(f"Epoch: [{epoch + 1}/{num_epochs}], Loss: {running_loss/100:.4f}, Acc: {100 * correct/total:.2f}%")
        
        running_loss = 0.0
            
        # 调整学习率
        scheduler.step()
   
    print("训练完成")

    # 保存模型
    model_path = os.path.join(script_dir, 'cifar10_cnn.pth')
    torch.save(model.state_dict(), model_path)
    print(f"模型已保存至 '{model_path}'")



# 6. 评估模型

def evaluate():
    '''在测试集上评估模型'''
    model.eval()
    test_loss = 0
    correct = 0
    total = 0

    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)

            # 前向传播
            outputs = model(images)

            # 计算损失
            loss = criterion(outputs, labels)
            test_loss += loss.item()

            # 统计准确率
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
        
    # 计算平均损失和准确率
    test_loss = test_loss / len(test_loader)
    accuracy = 100 * correct / total
    
    return test_loss, accuracy


# 7. 可视化模型预测

def visualize_predictions():
    """可视化模型在测试集上的预测结果"""
    model.eval()  # 设置为评估模式
    
    # 获取测试集图像
    dataiter = iter(test_loader)
    images, labels = next(dataiter)
    
    # 将图像移至指定设备
    images_on_device = images.to(device)
    
    # 获取模型预测
    with torch.no_grad():
        outputs = model(images_on_device)
        _, predicted = torch.max(outputs, 1)
    
    # 将图像移回CPU以便显示
    images = images.cpu()
    
    # 显示图像和预测
    plt.figure(figsize=(12, 4))
    
    # 显示8张图像
    for i in range(8):
        plt.subplot(2, 4, i + 1)
        imshow(images[i])
        color = 'green' if predicted[i] == labels[i] else 'red'
        plt.title(f'{classes[predicted[i]]}', color=color)
    
    plt.tight_layout()
    
    plt.show()



# 8. 分析每个类别的性能

def analyze_class_performance():
    """分析模型在每个类别上的性能"""
    model.eval()
    
    # 初始化类别预测统计
    class_correct = [0.] * 10
    class_total = [0.] * 10
    
    # 禁用梯度计算
    with torch.no_grad():
        for images, labels in test_loader:
            images, labels = images.to(device), labels.to(device)
            
            # 获取预测
            outputs = model(images)
            _, predicted = torch.max(outputs, 1)
            
            # 更新统计信息
            c = (predicted == labels).squeeze()
            for i in range(len(labels)):
                label = labels[i]
                class_correct[label] += c[i].item()
                class_total[label] += 1
    
    # 打印每个类别的准确率
    plt.figure(figsize=(10, 5))
    accuracies = []
    
    for i in range(10):
        accuracy = 100 * class_correct[i] / class_total[i]
        accuracies.append(accuracy)
        print(f'准确率 - {classes[i]}: {accuracy:.2f}%')
    
    # 绘制条形图
    plt.bar(classes, accuracies, color='skyblue')
    plt.xlabel('类别')
    plt.ylabel('准确率(%)')
    plt.title('每个类别的准确率')
    plt.ylim([0, 100])
    plt.xticks(rotation=45)
    
    plt.tight_layout()
    plt.show()


# 9. 模型训练入口

def main():

    # 可视化训练样本
    visualize_samples(train_loader)

    # 训练模型
    train(num_epochs=30)
    
    # 评估模型
    test_loss, test_accuracy = evaluate()
    print(f'损失: {test_loss/100:.4f}, 准确率: {test_accuracy:.2f}%')
    
    # 可视化预测结果
    visualize_predictions()
    
    # 分析每个类别的性能
    analyze_class_performance()


# 启动训练
if __name__ == "__main__":
    main()