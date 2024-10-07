package models

type MatchType struct {
	ID      uint64    `gorm:"primaryKey;autoIncrement" json:"id"`
	Name    string    `gorm:"type:varchar(45);unique" json:"name"`
	Matches []Matches `gorm:"foreignKey:MatchTypeId;references:ID"`
}
