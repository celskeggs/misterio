<?php
$redir_url = "http://" . $_SERVER['HTTP_HOST'] . rtrim(dirname($_SERVER['PHP_SELF']), '/\\');
function redirect($suffix) {
	global $redir_url;
	header("Location: $redir_url/$suffix");
}
$dbname = "spanish_mystery";
require("../dba.php");
session_start();
$access = false;
$admin_access = false;
$userid = 0;
$username = "Sr. An'onimo";
$useremail = null;
if (isset($_SESSION["token"])) {
	$qry = $db->prepare("SELECT `UID`, `Name`, `Email`, `Admin` FROM `Players` WHERE `Token`=?");
	$qry->bind_param("s", $_SESSION["token"]);
	$qry->execute();
	$qry->bind_result($qry_uid, $qry_name, $qry_email, $qry_admin);
	if ($qry->fetch()) {
		$access = true;
		$userid = $qry_uid;
		$username = $qry_name;
		$useremail = $qry_email;
		if ($qry_admin) {
			$admin_access = true;
		}
		if ($qry->fetch()) {
			echo "Authentication internal error: Double token.";
			$qry->close();
			die();
		}
	}
	$qry->close();
	if (!$access) {
		unset($_SESSION["token"]);
	}
}
if (!isset($req_access)) {
	echo "Access requestor required!";
	die();
}
if ($req_access === -1) {
	// Be logged out.
	if ($access) {
		redirect("index.php");
		die();
	}
} else if ($req_access === 0) {
	// Nothing needed.
} else if ($req_access === 1) {
	// Basic access needed.
	if (!$access) {
		redirect("login.php");
		die();
	}
} else if ($req_access === 2) {
	// Admin access needed.
	if (!($access && $admin_access)) {
		// TODO: Display better message
		redirect("login.php");
		die();
	}
} else {
	echo "Bad access requestor!";
	die();
}
?>
