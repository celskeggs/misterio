<?php
error_reporting(E_ALL);
ini_set("display_errors", "stdout");
$req_access = 1;
require('begin.php');
$pqry = $db->prepare("SELECT `IsPublic`,`Date`,`Contents`,`Name` FROM `Posts`,`Players` WHERE `Author`=`Players`.`UID` AND (`IsPublic` = 1 OR `Author`=?) ORDER BY `Date` ASC");
$pqry->bind_param("i", $userid);
$pqry->execute();
$pqry->bind_result($qry_ispublic, $qry_date, $qry_contents, $qry_author);
$posts = array();
while ($pqry->fetch()) {
	$posts[] = array($qry_ispublic, $qry_date, $qry_contents, $qry_author);
}
$pqry->close();
require('header.php');
?>
    <div id="title">Bienvenidos al Misterio en Cuzco, <?php echo htmlentities($username); ?></div>
    <div id="content">
<?php
if (count($posts) <= 0) {
?>
    <div id="noposts">No han nada postes</div>
<?php
} else {
	foreach ($posts as $post) {
		$postclasses = array("post");
		$ispublic = $post[0];
		if (!$ispublic) {
			$postclasses[] = "private";
		}
		$date = $post[1];
		$contents = $post[2];
		$author = $post[3];
?>
    <div class="<?php echo implode(' ', $postclasses); ?>">
      <div class="author"><?php echo htmlentities($author); ?></div>
      <div class="contents"><?php echo htmlentities($contents); ?></div>
    </div>
<?php
	}
}
?>
    </div>
<?php
  require('footer.php');
?>
