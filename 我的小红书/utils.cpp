//实现功能所需函数.cpp
#include <iostream>
#include <fstream>
#include <string>
#include <ctime>
#include <sstream>
using namespace std;


//全局变量区：
int sum1 = 0;//内容总数
int sum2 = 0;//博主与粉丝关系的个数
string phone_number, password, password1, nickname;


//结构体区：
struct Comments
{
	string blogger;
	string commentator;
	string comment;
};
struct Contents
{
	string time;
	string blogger;
	string content;
	Comments comments[200];
	int num = 0;//统计此内容的评论数量
}contents[1000];
struct Attentions
{
	string user;
	string blogger;
}attentions[1000];


//函数总区:
void loading()//加载数据(结构体从文件中获取数据)
{
	int j = 0;
	string a, b, c, d;
	ifstream in_file1("contents.txt", ios::in);
	while (1)
	{
		getline(in_file1, contents[sum1].blogger); getline(in_file1, contents[sum1].content); getline(in_file1, contents[sum1].time);
		if (in_file1.eof())break;
		sum1++;
	}
	in_file1.close();
	ifstream in_file2("comments.txt", ios::in);
	while (1)
	{
		getline(in_file2, a); getline(in_file2, b); getline(in_file2, c); getline(in_file2, d);
		if (in_file2.eof())break;
		for (j = 0; j < sum1; j++)
		{
			if (a == contents[j].blogger && b == contents[j].content)
			{
				contents[j].comments[contents[j].num].commentator = c;
				contents[j].comments[contents[j].num].comment = d;
				contents[j].num++;
				break;
			}
		}
	}
	in_file2.close();
	ifstream in_file3("follows.txt", ios::in);
	while (1)
	{
		getline(in_file3, attentions[sum2].user); getline(in_file3, attentions[sum2].blogger);
		if (in_file3.eof())break;
		sum2++;
	}
	in_file3.close();
}
void refreshing()//重整数据(更新文件信息)
{
	ofstream out_file1("contents.txt", ios::out);
	for (int i = 0; i < sum1; i++)out_file1 << contents[i].blogger << endl << contents[i].content << endl << contents[i].time << endl;
	out_file1.close();
	ofstream out_file2("comments.txt", ios::out);
	for (int i = 0; i < sum1; i++)
	{
		if (contents[i].num == 0)continue;
		else for (int j = 0; j < contents[i].num; j++)out_file2 << contents[i].blogger << endl << contents[i].content << endl << contents[i].comments[j].commentator << endl << contents[i].comments[j].comment << endl;
	}
	out_file2.close();
	ofstream out_file3("follows.txt", ios::out);
	for (int i = 0; i < sum2; i++)out_file3 << attentions[i].user << endl << attentions[i].blogger << endl;
	out_file3.close();
}
bool phone_number_legal(string a)//判断手机号是否合法
{
	int i = 0;
	while (a[i] != '\0')i++;
	if (i != 11)return 0;
	int x = 100 * (a[0] - '0') + 10 * (a[1] - '0') + a[2] - '0';//得到三位数
	if ((x >= 130 && x <= 139) || x == 147 || (x >= 149 && x <= 153) || (x >= 155 && x <= 159) || x == 173 || x == 177 || x == 180 || x == 181 || x == 185 || x == 186 || x == 188 || x == 189);
	else return 0;
	return 1;
}
bool phone_number_untapped(string x)//判断手机号是否未被注册过
{
	int i = 0;
	string a, b, c;
	ifstream in_file("users.txt", ios::in);
	while (1)
	{
		getline(in_file, a); getline(in_file, b); getline(in_file, c);
		if (in_file.eof()) { in_file.close(); return 1; }
		if (x == a) { in_file.close(); return 0; }
		i++;
	}
}
bool password_legal(string a)//判断密码是否合法
{
	int i = 0;
	while (a[i] != '\0')i++;
	if (i < 8)return 0;
	bool f1 = 0, f2 = 0, f3 = 0;
	for (int j = 0; j < i; j++)
	{
		if (a[j] >= 'a' && a[j] <= 'z')f1 = 1;
		if (a[j] >= 'A' && a[j] <= 'Z')f2 = 1;
		if (a[j] >= '0' && a[j] <= '9')f3 = 1;
	}
	if (f1 && f2 && f3)return 1;
	else return 0;
}
string captcha()//生成验证码
{
	string a;
	char ch;
	srand(time(NULL));
	for (int i = 0; i < 4; i++)
	{
		ch = 'A' + rand() % 26;
		a += ch;
	}
	return a;
}
bool match(string a, string b)//判断账号密码是否匹配
{
	int i = 0;
	string x, y, z;
	ifstream in_file("users.txt", ios::in);
	while (1)
	{
		getline(in_file, x); getline(in_file, y); getline(in_file, z);
		if (in_file.eof()) { in_file.close(); return 0; }
		if (a == x && b == y) { in_file.close(); return 1; }
		i++;
	}
}
void registration()//注册函数
{
	cout << "请进行注册:" << endl << endl;
	while (1)
	{
		cout << "请输入您的手机号码：" << endl << endl;
		getline(cin, phone_number);
		system("cls");
		if (!phone_number_legal(phone_number))cout << "注册失败，手机号码不合法，请重试" << endl << endl;
		else if (!phone_number_untapped(phone_number))cout << "注册失败，手机号码已被注册过，请重试" << endl << endl;
		else break;
		system("pause"); system("cls");
	}
	while (1)
	{
		cout << "请输入密码: (要求包含大小写字母和数字，并且长度至少8位)  " << endl << endl;
		getline(cin, password);
		system("cls");
		if (!password_legal(password)) { cout << "密码不合法，请重新输入" << endl << endl; continue; }
		cout << "请再次输入密码:" << endl << endl;
		getline(cin, password1);
		system("cls");
		if (password1 != password) cout << "两次输入密码不一致，请重试" << endl << endl;
		else break;
		system("pause"); system("cls");
	}
	while (1)
	{
		string a = captcha();
		cout << a << endl;
		cout << endl << "请输入上图中的验证码:" << endl << endl;
		string cap;
		getline(cin, cap);
		system("cls");
		for (int i = 0; cap[i] != '\0'; i++)if (cap[i] >= 'a')cap[i] += 'A' - 'a';
		if (cap != a)cout << "验证码错误，请重试" << endl << endl;
		else break;
		system("pause"); system("cls");
	}
	cout << "请您取一个昵称:" << endl << endl;
	getline(cin, nickname);
	system("cls");
	ofstream out_file("users.txt", ios::app);
	out_file << phone_number << endl << password << endl << nickname << endl;
	out_file.close();
}
void login(string* user, bool* legal_or_illegal)//登录函数
{
	cout << "请进行登录:" << endl << endl;
	while (1)
	{
		cout << "请输入您的账号(手机号):" << endl << endl;
		getline(cin, phone_number);
		system("cls");
		if (!phone_number_legal(phone_number))cout << "手机号不合法，请输入正确的手机号" << endl << endl;
		else if (phone_number_untapped(phone_number))cout << "手机号未注册，请重试" << endl << endl;
		else break;
		system("pause"); system("cls");
	}
	int errortimes = 0;
	while (1)
	{
		cout << "请输入您的密码：" << endl << endl;
		getline(cin, password);
		system("cls");
		if (!match(phone_number, password)) {
			errortimes++;
			if (errortimes == 3) {
				*legal_or_illegal = 0;
				cout << "连续3次密码输入错误，已强制退出应用" << endl;
				return;
			}
			cout << "密码不正确，当前已错误" << errortimes << "次，您还有" << 3 - errortimes << "次机会，请重试" << endl << endl;
		}
		else break;
	}
	ifstream in_file("users.txt", ios::in);
	string tmp1, tmp2, tmp3;
	while (1)
	{
		getline(in_file, tmp1); getline(in_file, tmp2); getline(in_file, tmp3);
		if (in_file.eof())return;
		if (tmp1 == phone_number && tmp2 == password){
			*user = tmp3;
			break;
		}
	}
}
void contents_launch(string nickname)//发布内容
{
	while (1)
	{
		cout << "请输入您想要发布的内容：" << endl << endl;
		string a;
		getline(cin, a);
		system("cls");
	flag1:
		cout << "输入1确认发布，输入0取消操作" << endl << endl;
		bool f = 0;
		string k;
		getline(cin, k);
		system("cls");
		if (k == "1")
		{
			cout << "发布成功！" << endl << endl;
			time_t now = time(nullptr);
			struct tm local_tm;
			errno_t err = localtime_s(&local_tm, &now);
			stringstream ss;
			ss << (local_tm.tm_year + 1900) << '-' << (local_tm.tm_mon + 1) << '-' << local_tm.tm_mday << ' ';
			ss << local_tm.tm_hour << ':' << local_tm.tm_min << ':' << local_tm.tm_sec;
			contents[sum1].time = ss.str();
			contents[sum1].blogger = nickname;
			contents[sum1].content = a;
			sum1++;
		}
		else if (k == "0") cout << "取消成功！" << endl << endl;
		else { cout << "输入错误，请按要求输入" << endl << endl; f = 1; }
		system("pause"); system("cls");
		if (f)goto flag1;
	flag2:
		cout << "输入1继续发布内容，输入0返回菜单" << endl << endl;
		getline(cin, k);
		system("cls");
		if (k == "0")break;
		else if (k == "1");
		else {
			cout << "输入错误，请按要求输入" << endl << endl;
			system("pause"); system("cls"); goto flag2;
		}
	}
}
void contents_delete(string nickname)//删除内容
{
	while (1)
	{
	flag1:
		int n = 0;//统计该用户发布的内容数
		int memory[1000];//记录目标内容在全部内容中的位置
		for (int i = sum1 - 1; i >= 0; i--)
		{
			if (contents[i].blogger == nickname) {
				n++; memory[n] = i;
				cout << n << ' ' << nickname << " : " << contents[i].content << "  " << contents[i].time << endl << endl;
			}
		}
		if (n == 0) {
			cout << "您未曾发布过内容，无法进行删除操作" << endl << endl;
			system("pause"); system("cls"); break;
		}
		cout << endl << endl << "以上为您发布过的内容" << endl << endl;
		cout << "请输入您想要删除内容的编号，输入0可返回菜单" << endl << endl;
		string a;
		getline(cin, a);
		system("cls");
		if (a.size() == 0) continue;
		int ii = 0;
		while (a[ii] != '\0')
		{
			if (a[ii] > '9' || a[ii] < '0') {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag1;
			}
			ii++;
		}
		int no = 0;
		for (int i = 0; i < ii; i++)no = 10 * no + a[i] - '0';
		if (no == 0)break;
		if (no > n) {
			cout << "编号不存在，请重试" << endl << endl;
			system("pause"); system("cls"); continue;
		}
	flag2:
		cout << "输入1确认删除，输入0取消操作" << endl << endl;
		getline(cin, a);
		system("cls");
		if (a == "1") {
			int key = memory[no];
			while (key < sum1)
			{
				contents[key] = contents[key + 1];
				key++;
			}//删除所选内容并补全
			sum1--;//内容数减少
			cout << "删除成功!" << endl << endl;
			system("pause"); system("cls");
		}
		else if (a == "0") {
			cout << "取消成功！" << endl << endl;
			system("pause"); system("cls");
		}
		else {
			cout << "输入错误，请按要求输入" << endl << endl;
			system("pause"); system("cls"); goto flag2;
		}
	}
}
void comments_reply(string nickname)//回复评论
{
	while (1)
	{
	flag1:
		int k = 0, v = 0;
		int memory[1000];//记录位置
		for (int i = 0; i < 30; i++)memory[i] = 0;
		for (int i = 0; i < sum1; i++)
		{
			if (contents[i].blogger == nickname) {
				v++;
				if (contents[i].num > 0) {
					k++; memory[k] = i;
					cout << k << ' ' << nickname << " : " << contents[i].content << "  " << contents[i].time << endl << endl;
				}
			}
		}
		if (v == 0){
			cout << "您未曾发布内容，无法进行此操作" << endl << endl;
			system("pause"); break;
		}
		if (k == 0){
			cout << "您发布的内容无人评论，无法进行此操作" << endl << endl;
			system("pause"); break;
		}
		cout << endl << endl << "您发布的以上内容有人评论过" << endl << endl << "请输入您想要回复的发布内容的编号，输入0可返回菜单" << endl << endl;
		string a;
		getline(cin, a);
		system("cls");
		if (a.size() == 0) continue;
		int ii = 0;
		while (a[ii] != '\0')
		{
			if (a[ii] > '9' || a[ii] < '0') {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag1;
			}
			ii++;
		}
		int no = 0;
		for (int i = 0; i < ii; i++)no = 10 * no + a[i] - '0';
		if (no == 0)break;
		if (no > k){
			cout << "编号不存在，请重试" << endl << endl;
			system("pause"); system("cls");
			continue;
		}
		no = memory[no];
	flag2:
		cout << nickname << " : " << contents[no].content << "  " << contents[no].time << endl << endl;
		cout << "评论：" << endl << endl;
		int j = 0;
		while (j < contents[no].num)
		{
			cout << j + 1 << ' ' << contents[no].comments[j].commentator << " : " << contents[no].comments[j].comment << endl << endl;
			j++;
		}
		cout << endl << endl << "请输入您想要回复的评论的编号，输入0返回上一级界面" << endl << endl;
		getline(cin, a);
		system("cls");
		if (a.size() == 0) goto flag2;
		ii = 0;
		while (a[ii] != '\0')
		{
			if (a[ii] > '9' || a[ii] < '0') {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag2;
			}
			ii++;
		}
		int kk = 0;
		for (int i = 0; i < ii; i++)kk = 10 * kk + a[i] - '0';
		if (kk == 0)continue;
		if (kk > j){
			cout << "编号不存在，请重试" << endl << endl;
			system("pause"); system("cls");
			goto flag2;
		}
		cout << "请回复：" << endl << endl;
		string cc;
		getline(cin, cc);
		system("cls");
	flag3:
		cout << "输入1确认回复，输入0取消操作" << endl << endl;
		getline(cin, a);
		system("cls");
		if (a == "1") {
			for (int s = contents[no].num; s > kk; s--)contents[no].comments[s] = contents[no].comments[s - 1];//向后移位，插入回复
			contents[no].comments[kk].commentator = nickname + "(回复" + contents[no].comments[kk - 1].commentator + ')';
			contents[no].comments[kk].comment = cc;
			contents[no].num++;
			cout << "回复成功！" << endl << endl;
			system("pause"); system("cls"); goto flag2;
		}
		else if (a == "0") { cout << "取消成功!" << endl << endl; system("pause"); system("cls"); goto flag2; }
		else {
			cout << "输入错误，请按要求输入" << endl << endl;
			system("pause"); system("cls"); goto flag3;
		}
	}
}
void surfing(string nickname)//查看其他用户发布内容
{
	while (1)
	{
	flag1:
		int n = 0, p = 0;
		string a;
		int memory[1000];//记录目标位置
		for (int i = sum1 - 1; i >= 0; i--)
		{
			if (contents[i].blogger != nickname){
				n++; memory[n] = i;
				cout << n << ' ' << contents[i].blogger << " : " << contents[i].content << "  " << contents[i].time << endl << endl;
			}
		}
		if (n == 0){
			cout << "暂无其他用户发布的内容" << endl << endl;
			system("pause");
			break;
		}
		cout << endl << endl << "以上是其他用户发布的内容，请输入您想要发表评论的内容的编号，输入0可返回菜单" << endl << endl;
		getline(cin, a);
		system("cls");
		if (a.size() == 0) continue;
		int ii = 0;
		while (a[ii] != '\0')
		{
			if (a[ii] > '9' || a[ii] < '0') {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag1;
			}
			ii++;
		}
		for (int i = 0; i < ii; i++)p = 10 * p + a[i] - '0';
		if (p == 0)break;
		if (p > n){
			cout << "编号不存在，请重试" << endl << endl;
			system("pause"); system("cls");
			continue;
		}
		p = memory[p];//得到内容位置
	flag2:
		cout << "(博主)" << ' ' << contents[p].blogger << " : " << contents[p].content << "  " << contents[p].time << endl << endl << "评论:" << endl << endl;
		for (int i = 0; i < contents[p].num; i++)cout << contents[p].comments[i].commentator << " : " << contents[p].comments[i].comment << endl << endl;
		cout << endl << endl << "输入1进行评论，输入0返回上一级界面" << endl << endl;
		getline(cin, a);
		system("cls");
		if (a == "0")continue;
		else if (a == "1") {
			cout << "请评论:" << endl << endl;
			string key;
			getline(cin, key);
			system("cls");
		flag3:
			cout << "输入1确定发表，输入0取消并返回上一级界面" << endl << endl;
			getline(cin, a);
			system("cls");
			if (a == "0")goto flag2;
			else if (a == "1") {
				contents[p].comments[contents[p].num].commentator = nickname;
				contents[p].comments[contents[p].num].comment = key;
				contents[p].num++;
				cout << "发表评论成功！" << endl << endl;
				system("pause"); system("cls");
				int j = 0;
				while (j < sum2)
				{
					if (attentions[j].user == nickname && attentions[j].blogger == contents[p].blogger)break;
					j++;
				}
				if (j == sum2) {
				flag4:
					cout << "是否关注此博主？ 输入1关注，输入0忽略" << endl << endl;
					getline(cin, a);
					system("cls");
					if (a == "1") {
						cout << "关注成功！" << endl << endl;
						attentions[sum2].user = nickname; attentions[sum2].blogger = contents[p].blogger;
						sum2++;
					}
					else if (a == "0") {
						cout << "已忽略" << endl << endl;
					}
					else {
						cout << "输入错误，请按要求输入" << endl << endl;
						system("pause"); system("cls"); goto flag4;
					}
					system("pause"); system("cls");
				}
				goto flag2;
			}
			else {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag3;
			}
		}
		else {
			cout << "输入错误，请按要求输入" << endl << endl;
			system("pause"); system("cls"); goto flag2;
		}
	}
}
void myattentions(string nickname)//查看关注用户的内容
{
	while (1)
	{
	flag1:
		int n = 0, m = 0;
		string a, b, c;
		int memory[300];//memorize内容的位置
		string memoryplus[300];//memorize的是关注博主的昵称
		for (int i = 0; i < sum2; i++)
		{
			if (attentions[i].user == nickname){
				n++;
				memoryplus[n] = attentions[i].blogger;
				cout << n << ' ' << attentions[i].blogger << endl << endl;
			}
		}
		if (n == 0){
			cout << "您没有关注过的博主，无法进行此操作" << endl << endl;
			system("pause");
			break;
		}
		cout << endl << endl << "以上是您关注过的博主，请输入您想查看博主的编号，输入0可返回菜单" << endl << endl;
		getline(cin, c);
		system("cls");
		if (c.size() == 0) continue;
		int ii = 0;
		while (c[ii] != '\0')
		{
			if (c[ii] > '9' || c[ii] < '0') {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag1;
			}
			ii++;
		}
		for (int i = 0; i < ii; i++)m = 10 * m + c[i] - '0';
		if (m == 0)break;
		if (m > n){
			cout << "编号不存在，请重试" << endl << endl;
			system("pause"); system("cls"); continue;
		}
		a = memoryplus[m];//记下查看博主的昵称
	flag2:
		n = 0;//赋0
		for (int i = sum1 - 1; i >= 0; i--)
		{
			if (a == contents[i].blogger){
				n++;
				memory[n] = i;
				cout << n << ' ' << a << " : " << contents[i].content << "  " << contents[i].time << endl << endl;
			}
		}
		if (n == 0){
			cout << "您关注的这个博主暂时未发布内容，按任意键返回上一级界面" << endl << endl;
			system("pause"); system("cls");
			continue;
		}
		cout << endl << endl << "以上为这个博主所发布过的内容，请输入您想评论内容的编号，输入0可返回上一级界面" << endl << endl;
		getline(cin, c);
		system("cls");
		if (c.size() == 0)  goto flag2;
		ii = 0, m = 0;
		while (c[ii] != '\0')
		{
			if (c[ii] > '9' || c[ii] < '0') {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag2;
			}
			ii++;
		}
		for (int i = 0; i < ii; i++)m = 10 * m + c[i] - '0';
		if (m == 0)continue;
		if (m > n){
			cout << "编号不存在，请重试" << endl << endl;
			system("pause"); system("cls"); goto flag2;
		}
		n = memory[m];//记下内容位置
	flag3:
		cout << "博主" << ' ' << a << " : " << contents[n].content << endl << endl << "评论:" << endl << endl;
		for (int i = 0; i < contents[n].num; i++)cout << contents[n].comments[i].commentator << " : " << contents[n].comments[i].comment << endl << endl;
		cout << endl << endl << "输入1进行评论，输入0返回上一级界面" << endl << endl;
		getline(cin, c);
		system("cls");
		ii = 0,m = 0;
		while (c[ii] != '\0')
		{
			if (c[ii] > '9' || c[ii] < '0') {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag3;
			}
			ii++;
		}
		for (int i = 0; i < ii; i++)m = 10 * m + c[i] - '0';
		if (m == 0)goto flag2;
		else if (m == 1) {
			cout << "请评论:" << endl << endl;
			getline(cin, b);
			system("cls");
		flag4:
			cout << "输入1确认发表评论，输入0取消操作" << endl << endl;
			getline(cin, c);
			system("cls");
			if (c == "0") {
				cout << "取消成功！" << endl << endl;
				system("pause"); system("cls"); goto flag3;
			}
			else if (c == "1"){
				cout << "发表成功！" << endl << endl;
				contents[n].comments[contents[n].num].commentator = nickname;
				contents[n].comments[contents[n].num].comment = b;
				contents[n].num++;
				system("pause"); system("cls"); goto flag3;
			}
			else {
				cout << "输入错误，请按要求输入" << endl << endl;
				system("pause"); system("cls"); goto flag4;
			}
		}
		else {
			cout << "输入错误，请按要求输入" << endl << endl;
			system("pause"); system("cls"); goto flag3;
		}
	}
}