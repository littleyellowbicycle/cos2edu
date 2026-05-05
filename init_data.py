import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.core.database import engine, Base, SessionLocal, init_db
from app.core.database import Character, Material, ModelConfig


def init_default_characters():
    db: Session = SessionLocal()
    try:
        existing = db.query(Character).first()
        if existing:
            print("角色已存在，跳过初始化")
            return
        
        default_characters = [
            {
                "name": "三月七",
                "avatar": "🌸",
                "description": "活泼可爱的元气少女",
                "personality": "活泼可爱，略带碎碎念，像个元气满满的小妹妹。对学生非常热情，总是用积极的语言鼓励对方。有时候会有点小迷糊，但在教学上非常认真负责。喜欢用轻松愉快的方式讲解知识，让学习变得有趣。",
                "background": "你是一位充满活力的AI导师，性格就像春天一样明媚。你相信学习应该是一件快乐的事情，所以总是努力让课堂变得生动有趣。你会用各种形象的比喻和例子来帮助学生理解抽象的概念。"
            },
            {
                "name": "刻晴",
                "avatar": "⚡",
                "description": "严格高效的完美主义者",
                "personality": "外冷内热，严格高效，是个完美主义者。对学生要求很高，但内心其实非常关心对方的成长。说话直接，不喜欢绕弯子，但会在学生遇到困难时给予最实际的帮助。注重效率，强调方法论。",
                "background": "你是一位追求卓越的AI导师，相信只有通过严格的训练才能真正掌握知识。你做事一丝不苟，对每个概念都要求学生透彻理解。虽然看起来很严厉，但当学生真正努力时，你会给予最真诚的认可。"
            },
            {
                "name": "苏格拉底",
                "avatar": "🧙‍♂️",
                "description": "经典苏格拉底式导师",
                "personality": "睿智、深邃、善于提问。你从不直接给出答案，而是通过一系列精心设计的问题引导学生自己思考。你相信真正的知识来自于内心的觉醒，而不是外在的灌输。你的提问总是恰到好处，能够启发学生的深度思考。",
                "background": "你是苏格拉底教学法的化身。两千多年前，苏格拉底在雅典的广场上通过提问来引导年轻人思考；今天，你通过数字化的方式延续这一传统。你相信，最好的教育不是灌输，而是点燃火焰。"
            }
        ]
        
        for char_data in default_characters:
            char = Character(**char_data)
            db.add(char)
        
        db.commit()
        print("已初始化默认角色")
    except Exception as e:
        print(f"初始化角色失败: {e}")
        db.rollback()
    finally:
        db.close()


def init_sample_material():
    db: Session = SessionLocal()
    try:
        existing = db.query(Material).first()
        if existing:
            print("教材已存在，跳过初始化")
            return
        
        sample_material = Material(
            title="卷积神经网络入门",
            description="介绍卷积神经网络的基本概念和工作原理",
            content="""## 卷积神经网络（CNN）简介

卷积神经网络（Convolutional Neural Network，简称CNN）是一种专门用于处理具有网格结构数据的神经网络，如图像（2D网格）、语音（1D网格）等。

### 核心概念

1. **卷积层（Convolutional Layer）**
   - 卷积层是CNN的核心组件
   - 使用滤波器（Filter/Kernel）在输入数据上滑动
   - 通过卷积操作提取特征
   - 例如：一个3x3的滤波器可以检测边缘、纹理等低级特征

2. **池化层（Pooling Layer）**
   - 用于降低特征图的空间维度
   - 常见的有最大池化（Max Pooling）和平均池化（Average Pooling）
   - 减少计算量，同时保留重要特征
   - 提供一定的平移不变性

3. **全连接层（Fully Connected Layer）**
   - 通常在网络的最后几层
   - 将卷积层提取的特征映射到最终的输出
   - 用于分类或回归任务

### 工作原理

想象一下，你有一张手写数字"5"的图片：
1. 第一层卷积可能检测到边缘、曲线等基本形状
2. 第二层卷积可能组合这些边缘，检测到圆圈、横线等更复杂的形状
3. 更高层的卷积可能检测到完整的数字结构
4. 最后全连接层将这些特征组合，判断这是数字"5"

### 为什么CNN适合图像处理？

1. **参数共享**：同一个滤波器在整张图片上共享，大大减少参数数量
2. **稀疏连接**：每个输出神经元只连接到输入的一小部分
3. **平移不变性**：通过池化操作，物体的位置变化不影响识别结果

### 常见的CNN架构

- LeNet-5：经典的手写数字识别网络
- AlexNet：2012年ImageNet竞赛冠军，深度CNN的里程碑
- VGGNet：使用统一的3x3卷积核，网络结构规整
- ResNet：引入残差连接，解决深度网络退化问题
- MobileNet：轻量化网络，适合移动设备

这就是卷积神经网络的基本概念。理解这些概念后，你就能更好地理解CNN是如何"看"图片的了。"""
        )
        
        db.add(sample_material)
        db.commit()
        print("已初始化示例教材")
    except Exception as e:
        print(f"初始化教材失败: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    print("正在初始化数据库...")
    init_db()
    
    print("正在初始化默认角色...")
    init_default_characters()
    
    print("正在初始化示例教材...")
    init_sample_material()
    
    print("初始化完成！")
    print("\n使用方法：")
    print("1. 安装依赖: pip install -r requirements.txt")
    print("2. 启动服务: python main.py")
    print("3. 访问 http://localhost:8000")


if __name__ == "__main__":
    main()
