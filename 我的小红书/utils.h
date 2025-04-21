//utils.h
#include<iostream>
#include <string>
using namespace std;

//注册与登录部分所需函数
bool phone_number_legal(string a);//判断手机号是否合法
bool phone_number_untapped(string a);//判断手机号是否未被注册过
bool password_legal(string a);//判断密码是否合法
bool match(string a, string b);//判断账号密码是否匹配
string captcha();//生成验证码

//沟通结构体与文件
void loading();//加载数据
void refreshing();//重整数据

//注册与登录
void registration();//注册
void login(string* user, bool* legal_or_illegal);//登录并获取用户昵称

//五大功能
void contents_launch(string nickname);//发布内容
void contents_delete(string nickname);//删除内容
void comments_reply(string nickname);//回复评论
void surfing(string nickname);//查看其他用户发布内容
void myattentions(string nickname);//查看关注用户的内容