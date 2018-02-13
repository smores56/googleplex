function submit_login() {
  var pass = document.getElementById('password').value;
  var email = document.getElementById('email').value;
  scrypt(pass, (email + 'xyz').substring(0, 8), {
    N: 4,
    r: 4,
    p: 2,
    dkLen: 16,
    encoding: 'hex'
  }, function(hash) {
    document.getElementById('pass_hash').value = hash;
    document.getElementById('login-form').submit(); //form submission
  });
}
