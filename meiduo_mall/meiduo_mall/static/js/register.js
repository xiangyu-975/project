let vm = new Vue({
    el: '#app',
    // 修改Vue语法
    delimiters: ['[[', ']]'],
    data: {
        // v-model
        username: '',
        password: '',
        password2: '',
        mobile: '',
        allow: '',
        image_code_url:'',
        uuid:'',
        image_code:'',

        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        error_image_code : false,

        error_name_message: '',
        error_mobile_message: '',
        error_image_code_message:'',
    },
    mounted(){  // 页面加载完被调用
        // 生成图形验证码
        this.generate_image_code();
    },
    methods: {
        // 生成图形验证码
        // 封装思想，代码复用
        generate_image_code(){
          // 生成UUID. generateUUID():  封装common.js文件中，需要提前引入
            this.uuid = generateUUID();
            // 拼接图形验证码请求地址
            this.image_code_url = '/image_codes/' + this.uuid + '/';
        },

        // 检验用户名
        check_username() {
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if (re.test(this.username)) {
                this.error_name = false;
            } else {
                this.error_name_message = '请输入5-20个字符的用户名';
                this.error_name = true;
            }
            if (this.error_name == false) { // 只有当用户输入的用户名满足条件是才判断
                let url = '/usernames/' + this.username + '/count/';
                axios.get(url, {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.count == 1) {
                            this.error_name_message = '用户名已存在';
                            this.error_name = true;
                        } else {
                            this.error_name = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response);
                    })
            }
        },

        // 检验密码
        check_password() {
            let re = /^[a-zA-Z0-9]{8,20}$/;
            if (re.test(this.password)) {
                this.error_password = false;
            } else {
                this.error_password = true;
            }
        },
        // 检验确认密码
        check_password2() {
            if (this.password != this.password2) {
                this.error_password2 = true;
            } else {
                this.password2 = false;
            }
        },
        // 检验手机号
        check_mobile() {
            let re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_mobile_message = '您输入的手机号格式不正确';
                this.error_mobile = true;
            }
            if (this.error_mobile == false) {
                let url = '/mobiles/' + this.mobile + '/count/';
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
        check_image_code(){
            if (this.image_code.length != 4) {
                this.error_image_code_message = '请填写图片验证码';
                this.error_image_code = true;
            } else {
                this.error_image_code = false;
            }
        },
        // 检验勾选协议
        check_allow() {
            if (!this.allow) {
                this.error_allow = true;
            } else {
                this.error_allow = false;
            }
        },
        // 监听表单数据
        on_submit() {
            this.check_username();
            this.check_password();
            this.check_password2();
            this.check_mobile();
            this.check_allow();

            if (this.error_name == true || this.error_password == true || this.error_password2 == true ||
                this.error_mobile == true || this.error_allow == true) {
                // 禁止表单提交
                window.event.returnValue = false;
            }
        },
    }


});



