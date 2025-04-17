import torch  # Pytorch核心库
import torch.nn as nn  # 神经网络模块
import torch.optim as optim  # 优化器模块
import torchvision  # 用于处理图像的库
import torchvision.transforms as transforms  # 用于图像变换的工具
from torch.utils.data import DataLoader  # 数据加载器
import numpy as np
import matplotlib.pyplot as plt
import os

script_dir = os.path.dirname(os.path.abspath(__file__))

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
print(f"使用设备: {device}")

# 定义数据预处理步骤
transform = transforms.Compose([
    transforms.ToTensor(),  # 将图像转换为Pytorch张量
    transforms.Normalize((0.1307,), (0.3081,))  # 标准化图像数据
])
# 下载训练集和测试集
train_dataset = torchvision.datasets.MNIST(
    root=os.path.join(script_dir, 'data'),  # 指定存储路径
    train=True,  # 指定训练集
    download=True,  # 如果数据不存在则下载
    transform=transform  # 应用上面定义的变换
)
test_dataset = torchvision.datasets.MNIST(
    root=os.path.join(script_dir, 'data'),  # 指定存储路径
    train=False,  # 指定测试集
    download=True, 
    transform=transform
)
# 创建数据加载器
batch_size = 64  # 每批处理的样本数
train_loader = DataLoader(
    train_dataset,
    batch_size=batch_size,
    shuffle=True  # 随机打乱数据
)
test_loader = DataLoader(
    test_dataset,
    batch_size=batch_size,
    shuffle=False  # 测试集不需要打乱
)

# 打印数据集信息
print(f"训练集大小: {len(train_dataset)}")
print(f"测试集大小: {len(test_dataset)}")
print(f"图像大小: {train_dataset[0][0].shape}")  # [1, 28, 28] - [通道数, 高度, 宽度]
print(f"类别数量: {len(train_dataset.classes)}")  # 10类 (0-9)


# 定义一个简单的全连接神经网络

class SimpleNN(nn.Module):  # 所有神经网络模块的基类，我们的模型继承自它
    def __init__(self):
        super().__init__()
        self.fc1 = nn.Linear(28 * 28, 128)  # 第一个全连接层: 输入尺寸 28x28=784, 输出尺寸 128
        self.fc2 = nn.Linear(128, 64)  # 第二个全连接层: 输入尺寸 128, 输出尺寸 64
        self.fc3 = nn.Linear(64, 10)  # 输出层: 输入尺寸 64, 输出尺寸 10 (对应10个数字类别)

        self.relu = nn.ReLU()  # ReLU激活函数  f(x) = max(0, x)

    def forward(self, x):
        '''定义正向传播过程，当调用模型实例时会自动执行'''
        x = x.view(-1, 28 * 28)  # 首先将28x28的图像展平为一维向量
        x = self.relu(self.fc1(x))  # 通过第一层和激活函数
        x = self.relu(self.fc2(x))  # 通过第二层和激活函数
        x = self.fc3(x)  # 输出层 (不使用激活函数，因为后面会用交叉熵损失函数)

        return x
    

# 创建模型实例并移至指定设备
model = SimpleNN().to(device)
print(model)


# 定义损失函数和优化器

# 损失函数：交叉熵损失
criterion = nn.CrossEntropyLoss()  # 分类问题常用的损失函数，结合了LogSoftmax和负对数似然损失

# 优化器：随机梯度下降
optimizer = optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
# optim.SGD：随机梯度下降优化器
# model.parameters()：获取模型中所有可训练的参数
# lr：学习率，控制参数更新步长
# momentum：动量因子，加速收敛并帮助逃离局部最小值

# 也可使用 Adam优化器
# optimizer = optim.Adam(model.parameters(), lr=0.001)


# 训练函数
def train(num_epochs):
    '''训练模型函数'''
    print("开始训练...")

    # 遍历训练周期
    for epoch in range(num_epochs):
        running_loss = 0.0

        # 遍历批次数据
        for i, data in enumerate(train_loader):
            # 获取输入和标签，并移至指定设备
            inputs, labels = data
            inputs, labels = inputs.to(device), labels.to(device)
        
            # 梯度清零 否则会累积
            optimizer.zero_grad()  # 清除之前计算的梯度

            # 前向传播
            outputs = model(inputs)  # 调用模型的forward方法

            # 计算损失
            loss = criterion(outputs, labels)

            # 反向传播
            loss.backward()  # 反向传播，计算梯度

            # 更新权重
            optimizer.step()  # 根据梯度更新模型参数

            # 累计损失
            running_loss += loss.item()  # 获取损失值（标量）

            # 每100个批次打印一次信息
            if (i + 1) % 100 ==0:
                print(f"Epoch: [{epoch + 1}/{num_epochs}]  Step: [{i + 1}/{len(train_loader)}]  Loss: {running_loss / 100:.4f}")
                running_loss = 0
    
    print("训练结束")

    # 保存模型
    model_path = os.path.join(script_dir, 'mnist_model.pth')
    torch.save(model.state_dict(), model_path)  # 保存模型参数到文件
    print("模型已保存为 'mnist_model.pth'")

# 训练周期 (3个周期)
train(num_epochs=3)


# 评估函数
def evaluate():
    '''评估模型函数'''
    model.eval()  # 将模型设置为评估模式，禁用dropout等

    correct = total = 0

    # 在测试时不需要计算梯度
    with torch.no_grad():  # 禁用梯度计算，减少内存使用并加速计算
        for data in test_loader:
            images, labels = data
            images, labels = images.to(device), labels.to(device)

            # 前向传播
            outputs = model(images)

            # 获取预测结果
            _, predicted = torch.max(outputs.data, 1)  # 沿指定维度找出最大值和索引，返回值为(max_values, max_indices)

            # 统计总样本数和正确样本数
            total += labels.size(0)
            correct += (predicted == labels).sum().item()  # 比较预测值和真实标签 + 计算匹配的总数
    
    accuracy = 100 * correct / total
    print(f"测试集精度: {accuracy:.2f}%")

# 评估模型
evaluate()


# 可视化预测结果
def visualize_predictions():
    '''可视化预测结果'''
    model.eval()

    # 取一批测试数据
    dataiter = iter(test_loader)  # 创建一个迭代器
    images, labels = next(dataiter)  # 获取下一批数据
    images, labels = images.to(device), labels.to(device)

    # 预测
    outputs = model(images)
    _, predicted = torch.max(outputs, 1)  # 获取每行的最大值(即预测概率)及其索引(即预测类别)

    # 显示图像和预测结果
    plt.figure(figsize=(12, 6))
    for i in range(12):  # 显示12张图像
        plt.subplot(3, 4, i + 1)
        
        # 将图像从tensor转为numpy，并重新调整形状以显示
        img = images[i].cpu().squeeze().numpy()  # squeeze()：去除大小为1的维度
        
        plt.imshow(img, cmap='gray')
        plt.title(f'预测: {predicted[i].item()}, 实际: {labels[i].item()}')
        plt.axis('off')
    
    img_path = os.path.join(script_dir, 'predictions.png')

    plt.tight_layout()
    plt.savefig(img_path)
    plt.show()

visualize_predictions()


# 加载保存的模型并进行预测
def load_and_predict():
    """加载保存的模型并进行预测"""
    # 创建一个新的模型实例
    loaded_model = SimpleNN().to(device)
    
    # 加载保存的模型参数
    model_path = os.path.join(script_dir, 'mnist_model.pth')
    loaded_model.load_state_dict(torch.load(model_path))  # 从文件加载模型参数
    
    # 设置为评估模式
    loaded_model.eval()
    
    # 随机选择一张测试图像
    idx = np.random.randint(0, len(test_dataset))
    image, true_label = test_dataset[idx]
    
    # 添加batch维度并移至指定设备
    image = image.unsqueeze(0).to(device)  # unsqueeze(0)：添加一个维度，将单个图像转换为批次格式
    
    # 预测
    with torch.no_grad():
        output = loaded_model(image)
        _, predicted = torch.max(output, 1)
    
    # 显示结果
    plt.figure()
    plt.imshow(image.cpu().squeeze(), cmap='gray')
    plt.title(f'预测: {predicted.item()}, 实际: {true_label}')
    plt.axis('off')
    plt.show()
    
    print(f'预测结果: {predicted.item()}')
    print(f'实际标签: {true_label}')

# 加载模型并预测
load_and_predict()