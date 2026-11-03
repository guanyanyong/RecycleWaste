-- ============================================================
-- 业务扩展表（原建表脚本未覆盖，按业务场景补充）
-- 说明：weigh_trip/weigh_item 中的 customer_id 需要落地实体，
--       业务场景要求「按姓名或手机号识别客户」，故补充客户表；
--       vehicle_id 同理补充车辆表（车牌快照仍保留在行程上）。
-- 幂等：CREATE TABLE IF NOT EXISTS，可重复执行。
-- ============================================================

SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS `biz_customer` (
  `customer_id`   BIGINT       NOT NULL AUTO_INCREMENT COMMENT '客户ID',
  `tenant_id`     BIGINT       NOT NULL COMMENT '所属租户',
  `customer_code` VARCHAR(50)  NOT NULL COMMENT '客户编码,租户内唯一',
  `customer_name` VARCHAR(100) NOT NULL COMMENT '客户/供应商姓名或公司名',
  `phone`         VARCHAR(20)  DEFAULT NULL COMMENT '手机号,用于现场识别',
  `id_card`       VARCHAR(30)  DEFAULT NULL COMMENT '身份证号(可选)',
  `customer_type` TINYINT      NOT NULL DEFAULT 1 COMMENT '1=个人 2=企业',
  `address`       VARCHAR(200) DEFAULT NULL COMMENT '地址',
  `status`        TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=启用',
  `remark`        VARCHAR(200) DEFAULT NULL COMMENT '备注',
  `create_time`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`customer_id`),
  UNIQUE KEY `uk_tenant_code` (`tenant_id`,`customer_code`),
  KEY `idx_tenant_phone` (`tenant_id`,`phone`),
  KEY `idx_tenant_name` (`tenant_id`,`customer_name`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='客户/供应商表';

CREATE TABLE IF NOT EXISTS `biz_vehicle` (
  `vehicle_id`        BIGINT       NOT NULL AUTO_INCREMENT COMMENT '车辆ID',
  `tenant_id`         BIGINT       NOT NULL COMMENT '所属租户',
  `plate_no`          VARCHAR(20)  NOT NULL COMMENT '车牌号,租户内唯一',
  `vehicle_type`      VARCHAR(30)  DEFAULT NULL COMMENT '车型',
  `tare_weight`       DECIMAL(12,2) DEFAULT NULL COMMENT '备案皮重(吨)',
  `owner_customer_id` BIGINT       DEFAULT NULL COMMENT '所属客户',
  `status`            TINYINT      NOT NULL DEFAULT 1 COMMENT '0=停用 1=启用',
  `create_time`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `update_time`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  PRIMARY KEY (`vehicle_id`),
  UNIQUE KEY `uk_tenant_plate` (`tenant_id`,`plate_no`),
  KEY `idx_tenant_customer` (`tenant_id`,`owner_customer_id`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci COMMENT='车辆表';

-- 演示客户（tenant_id=1）
INSERT INTO `biz_customer` (`tenant_id`,`customer_code`,`customer_name`,`phone`,`customer_type`,`address`,`status`)
SELECT 1,'C0001','张建国','13800001111',1,'深圳市南山区',1 FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `biz_customer` WHERE `tenant_id`=1 AND `customer_code`='C0001');

INSERT INTO `biz_customer` (`tenant_id`,`customer_code`,`customer_name`,`phone`,`customer_type`,`address`,`status`)
SELECT 1,'C0002','李秀兰','13800002222',1,'深圳市宝安区',1 FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `biz_customer` WHERE `tenant_id`=1 AND `customer_code`='C0002');

INSERT INTO `biz_customer` (`tenant_id`,`customer_code`,`customer_name`,`phone`,`customer_type`,`address`,`status`)
SELECT 1,'C0003','顺发废品回收站','13800003333',2,'深圳市龙岗区',1 FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `biz_customer` WHERE `tenant_id`=1 AND `customer_code`='C0003');

INSERT INTO `biz_customer` (`tenant_id`,`customer_code`,`customer_name`,`phone`,`customer_type`,`address`,`status`)
SELECT 1,'C0004','王海涛','13800004444',1,'深圳市福田区',1 FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `biz_customer` WHERE `tenant_id`=1 AND `customer_code`='C0004');

-- 演示车辆（tenant_id=1）
INSERT INTO `biz_vehicle` (`tenant_id`,`plate_no`,`vehicle_type`,`tare_weight`,`owner_customer_id`,`status`)
SELECT 1,'粤B12345','轻型货车',3.50,1,1 FROM DUAL
WHERE NOT EXISTS (SELECT 1 FROM `biz_vehicle` WHERE `tenant_id`=1 AND `plate_no`='粤B12345');
