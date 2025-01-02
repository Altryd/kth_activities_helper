package models

type Role struct {
	ID    int    `gorm:"primaryKey;autoIncrement" json:"id"`
	Name  string `gorm:"type:varchar(45);unique" json:"name"`
	Users []User `gorm:"foreignKey:RoleId;references:ID"`
}
