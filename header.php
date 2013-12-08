<!DOCTYPE html>
<html>
  <head>
    <title>Un Misterio en Cuzco<?php if (isset($title)) { echo ": $title"; } ?></title>
    <link rel="stylesheet" href="style.css" type="text/css">
  </head>
  <body>
<?php
if (isset($_GET['msg'])) {
	$hide = "http://" . $_SERVER['HTTP_HOST'] . $_SERVER['PHP_SELF'];
	echo "<div id='msg'>" . htmlentities($_GET['msg']) . " <a href='$hide'>[X]</a></div>";
}
?>
