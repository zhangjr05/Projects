#include <iostream>
#include <string>
#include <fstream>
#include "utils.h"
using namespace std;
string user;
int main()
{
	loading();//加载：将文件信息转移到结构体中
Flag2:
	cout << "小红书:你的生活指南" << endl << endl;
	cout << "如果已有账号，输入1进行登录" << endl;
	cout << "如果您是新用户，请输入0先进行注册" << endl;
	cout << "退出应用程序，请输入-1" << endl << endl;
	string u;
	getline(cin, u);
	system("cls");
	if (u == "-1"){
		cout << "欢迎下次使用！" << endl;
		refreshing();//重整，更新文件信息
		return 0;
	}
	else if (u == "1")goto Flag3;//跳转到登录界面
	else if (u == "0");
	else
	{
		cout << "输入错误，请按要求输入" << endl << endl;
		system("pause"); system("cls");
		goto Flag2;
	}
	registration();//注册环节
Flag3:
	bool legal_or_illegal = 1;//判断用户是否正常登录
	login(&user, &legal_or_illegal);//登录环节
	if (!legal_or_illegal)return -1;//判断用户是否正常登录
	cout << "登录成功！" << endl;
	cout << "欢迎您，" << user << endl << endl;
Flag1:
	cout << "菜 单 栏" << endl << endl;
	cout << "退出应用程序，请输入-1" << endl << endl;
	cout << "退出登录，请输入0" << endl << endl;
	cout << "发布内容，请输入1" << endl << endl;
	cout << "删除内容，请输入2" << endl << endl;
	cout << "回复评论，请输入3" << endl << endl;
	cout << "查看其他用户发布内容，请输入4" << endl << endl;
	cout << "查看关注用户的内容，请输入5" << endl << endl << endl;
	string click;
	getline(cin, click);
	system("cls");
	if (click == "-1") {
		cout << "欢迎下次使用！" << endl;
		refreshing();//重整，更新文件信息
		return 0;
	}
	else if (click == "0")goto Flag2;
	else if (click == "1")contents_launch(user);
	else if (click == "2")contents_delete(user);
	else if (click == "3")comments_reply(user);
	else if (click == "4")surfing(user);
	else if (click == "5")myattentions(user);
	else { cout << "输入错误，请按要求输入" << endl << endl; system("pause"); }
	system("cls");
	goto Flag1;//重回菜单界面
}