// 采用ES6语法
// 创建Vue对象 vm
let vm = new Vue({
    el: '#app', // 通过ID选择器找到绑定的HTML内容
    delimiters: ['[[', ']]'],
    data: {// 数据对象
        // v-model
        username: '',
        password: '',
        password2: '',
        mobile: '',
        allow: '',
        image_code_url: '',
        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        // error_message
        error_name_message: '',
        error_mobile_message: '',
    },
    methods: {  // 定义和实现事件方法
        // 校验用户名
        check_username(){
            // 用户名5——20个字符，[a-zA-Z0-9_-]
            // 定义正则
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            // 使用正则匹配用户名数据
            if (re.test(this.username)) {
                // 匹配成功，不展示错误信息
                this.error_name = false;
            } else {
                // 匹配失败，展示错误信息
                this.error_name_message = '请输入5-20个字符的用户名';
                this.error_name = true;
            }
            // 检验用户名是否重复注册
            if (this.error_name == false) {// 只有当用户输入的用户名满足条件时才去判断
                let url = '/usernames/' + this.username + '/count/';
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.count == 1) {
                            // 用户名已存在
                            this.error_name_message = '用户名已存在';
                            this.error_name = true;
                        } else {
                            // 用户名不存在
                            this.error_name = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response)
                    })
            }
        },
        // 校验密码
        check_password() {
            let re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)) {
                this.error_password = false;
            } else {
                this.error_password = true;
            }
        },
        // 校验确认密码
        check_password2() {
            if (this.password != this.password2) {
                this.error_password2 = true;
            } else {
                this.error_password2 = false;
            }
        },
        // 校验手机号
        check_mobile() {
            let re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_mobile_message = '您输入的手机号格式不正确';
                this.error_mobile = true;
            }
            if (this.error_mobile == false) {
                let url = '/mobiles/'+ this.mobile + '/count/';
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.count == 1) {
                            this.error_mobile_message = '手机号已存在';
                            this.error_mobile = true;
                        } else {
                            this.error_mobile = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                    })
            }
        },
        // 校验是否勾选协议
        check_allow() {
            if (!this.allow) {
                this.error_allow = true;
            } else {
                this.error_allow = false;
            }
        },
        // 监听表单提交事件
        on_submit() {
            this.check_username();
            this.check_password();
            this.check_password2();
            this.check_mobile();
            this.check_allow();

            // 在校验之后，注册数据中，只要有错误，就禁用表单的提交事件
            if (this.error_name == true || this.error_password == true || this.error_password2 == true ||
                this.error_mobile == true || this.error_allow == true) {
                // 禁用表单提交
                window.event.returnValue = false;
            }
        },
    }

});