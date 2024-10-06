package models

import "time"

type Matches struct {
	Id             uint64           `gorm:"primaryKey;autoIncrement:false" json:"id"`
	IsApproved     bool             `gorm:"default:false" json:"is_approved"`
	MatchTypeId    uint             `json:"match_type_id"`
	Date           time.Time        `gorm:"type:date" json:"date"`
	MatchUserScrim []MatchUserScrim `gorm:"foreignKey:MatchId;references:Id"`
}
