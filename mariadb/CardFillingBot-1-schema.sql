-- MySQL dump 10.13  Distrib 8.0.31, for macos12.6 (x86_64)
--
-- Host: 192.168.88.101    Database: CardFillingBot
-- ------------------------------------------------------
-- Server version	5.5.5-10.9.3-MariaDB-1:10.9.3+maria~ubu2204

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `apscheduler_jobs`
--

DROP TABLE IF EXISTS `apscheduler_jobs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `apscheduler_jobs` (
  `id` varchar(191) NOT NULL,
  `next_run_time` double DEFAULT NULL,
  `job_state` blob NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_apscheduler_jobs_next_run_time` (`next_run_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `budget`
--

DROP TABLE IF EXISTS `budget`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `budget` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fill_scope` int(11) NOT NULL,
  `category_code` varchar(255) NOT NULL,
  `monthly_limit` float NOT NULL,
  PRIMARY KEY (`id`),
  KEY `fill_scope` (`fill_scope`),
  KEY `category_code` (`category_code`),
  CONSTRAINT `budget_ibfk_1` FOREIGN KEY (`fill_scope`) REFERENCES `fill_scope` (`scope_id`),
  CONSTRAINT `budget_ibfk_2` FOREIGN KEY (`category_code`) REFERENCES `category` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=11 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `card_fill`
--

DROP TABLE IF EXISTS `card_fill`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `card_fill` (
  `fill_id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `fill_date` datetime NOT NULL,
  `amount` float NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  `category_code` varchar(255) DEFAULT 'OTHER',
  `fill_scope` int(11) NOT NULL DEFAULT 1,
  PRIMARY KEY (`fill_id`),
  KEY `user_id` (`user_id`),
  KEY `category_code` (`category_code`),
  KEY `fill_scope` (`fill_scope`),
  CONSTRAINT `card_fill_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `telegram_user` (`user_id`),
  CONSTRAINT `card_fill_ibfk_2` FOREIGN KEY (`category_code`) REFERENCES `category` (`code`),
  CONSTRAINT `card_fill_ibfk_3` FOREIGN KEY (`fill_scope`) REFERENCES `fill_scope` (`scope_id`)
) ENGINE=InnoDB AUTO_INCREMENT=2367 DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `category`
--

DROP TABLE IF EXISTS `category`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `category` (
  `code` varchar(255) NOT NULL,
  `name` varchar(255) NOT NULL,
  `aliases` text NOT NULL DEFAULT '',
  `proportion` decimal(3,2) NOT NULL DEFAULT 1.00,
  `emoji_name` varchar(255) NOT NULL DEFAULT ':red_question_mark:',
  PRIMARY KEY (`code`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `fill_scope`
--

DROP TABLE IF EXISTS `fill_scope`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fill_scope` (
  `scope_id` int(11) NOT NULL AUTO_INCREMENT,
  `scope_type` varchar(255) NOT NULL,
  `chat_id` int(11) NOT NULL,
  `description` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`scope_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Temporary view structure for view `monthly_report_by_category`
--

DROP TABLE IF EXISTS `monthly_report_by_category`;
/*!50001 DROP VIEW IF EXISTS `monthly_report_by_category`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `monthly_report_by_category` AS SELECT 
 1 AS `rownumber`,
 1 AS `fill_scope`,
 1 AS `fill_year`,
 1 AS `month_num`,
 1 AS `category_code`,
 1 AS `amount`,
 1 AS `monthly_limit`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `monthly_report_by_user`
--

DROP TABLE IF EXISTS `monthly_report_by_user`;
/*!50001 DROP VIEW IF EXISTS `monthly_report_by_user`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `monthly_report_by_user` AS SELECT 
 1 AS `rownumber`,
 1 AS `fill_scope`,
 1 AS `fill_year`,
 1 AS `month_num`,
 1 AS `user_id`,
 1 AS `amount`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `purchase`
--

DROP TABLE IF EXISTS `purchase`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `purchase` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fill_scope` int(11) NOT NULL,
  `name` varchar(255) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `purchase_fill_scopes` (`fill_scope`),
  CONSTRAINT `purchase_fill_scopes` FOREIGN KEY (`fill_scope`) REFERENCES `fill_scope` (`scope_id`)
) ENGINE=InnoDB AUTO_INCREMENT=34 DEFAULT CHARSET=utf8mb4;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `telegram_user`
--

DROP TABLE IF EXISTS `telegram_user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `telegram_user` (
  `user_id` int(11) NOT NULL,
  `is_bot` tinyint(1) NOT NULL,
  `first_name` varchar(255) DEFAULT NULL,
  `last_name` varchar(255) DEFAULT NULL,
  `username` varchar(255) DEFAULT NULL,
  `language_code` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Final view structure for view `monthly_report_by_category`
--

/*!50001 DROP VIEW IF EXISTS `monthly_report_by_category`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `monthly_report_by_category` AS select row_number() over ( partition by NULL order by NULL) AS `rownumber`,`cf`.`fill_scope` AS `fill_scope`,year(`cf`.`fill_date`) AS `fill_year`,month(`cf`.`fill_date`) AS `month_num`,`cat`.`code` AS `category_code`,sum(`cf`.`amount`) AS `amount`,`b`.`monthly_limit` AS `monthly_limit` from ((`card_fill` `cf` join `category` `cat` on(`cat`.`code` = `cf`.`category_code`)) left join `budget` `b` on(`b`.`fill_scope` = `cf`.`fill_scope` and `b`.`category_code` = `cat`.`code`)) group by `cf`.`fill_scope`,year(`cf`.`fill_date`),month(`cf`.`fill_date`),`cat`.`name`,`cat`.`proportion`,`b`.`monthly_limit` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `monthly_report_by_user`
--

/*!50001 DROP VIEW IF EXISTS `monthly_report_by_user`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`%` SQL SECURITY DEFINER */
/*!50001 VIEW `monthly_report_by_user` AS select row_number() over ( partition by NULL order by NULL) AS `rownumber`,`cf`.`fill_scope` AS `fill_scope`,year(`cf`.`fill_date`) AS `fill_year`,month(`cf`.`fill_date`) AS `month_num`,`tuser`.`user_id` AS `user_id`,sum(`cf`.`amount`) AS `amount` from (`card_fill` `cf` join `telegram_user` `tuser` on(`tuser`.`user_id` = `cf`.`user_id`)) group by `cf`.`fill_scope`,`tuser`.`username`,year(`cf`.`fill_date`),month(`cf`.`fill_date`) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2022-10-16 14:19:47
