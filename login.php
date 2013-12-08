<?php
if (isset($_GET['token'])) {
	session_start();
	$_SESSION["token"] = $_GET["token"];
}
$req_access = -1;
require('begin.php');
$title = "Login";
require('header.php');
?>
<div id="content">
You are not logged in!
To log in, check your email for the most recent login link.
[Needs spanish translation]
</div>
<?php
require("footer.php");
?>
