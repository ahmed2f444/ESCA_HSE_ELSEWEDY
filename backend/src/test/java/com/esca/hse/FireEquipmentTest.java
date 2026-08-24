package com.esca.hse;

import com.esca.hse.model.FireEquipment;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

public class FireEquipmentTest {

    @Test
    void fireEquipmentCanBeCreated() {
        FireEquipment equipment = new FireEquipment();
        equipment.setEquipmentId("FE-1001");
        equipment.setAssetTypeId("CO2");
        equipment.setStatus("VALID");

        assertEquals("FE-1001", equipment.getEquipmentId());
        assertEquals("CO2", equipment.getAssetTypeId());
        assertEquals("VALID", equipment.getStatus());
    }
}
