// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title EnergyToken
 * @dev ERC-20 token representing solar energy credits
 * 1 token = 1 kWh of solar energy
 */
contract EnergyToken is ERC20, ERC20Burnable, Ownable {

    // Events
    event EnergyMinted(address indexed seller, uint256 amount, string metadata);
    event EnergyPurchased(address indexed buyer, address indexed seller, uint256 amount, uint256 price);
    event EnergyConsumed(address indexed consumer, uint256 amount);

    // Mapping to track energy production by sellers
    mapping(address => uint256) public totalEnergyProduced;

    // Mapping to track energy consumption by buyers
    mapping(address => uint256) public totalEnergyConsumed;

    /**
     * @dev Constructor
     * @param initialOwner Address of the contract owner (platform)
     */
    constructor(address initialOwner)
        ERC20("Solar Energy Credit", "SEC")
        Ownable(initialOwner)
    {
        // Token symbol: SEC (Solar Energy Credit)
        // Decimals: 18 (standard for ERC-20)
    }

    /**
     * @dev Mint new energy tokens when seller produces energy
     * @param to Address of the seller (energy producer)
     * @param amount Amount of energy in kWh (will be converted to tokens)
     * @param metadata Additional information (e.g., production date, solar panel ID)
     */
    function mintEnergy(
        address to,
        uint256 amount,
        string memory metadata
    ) public onlyOwner {
        require(to != address(0), "Cannot mint to zero address");
        require(amount > 0, "Amount must be greater than zero");

        // Convert kWh to tokens (1 kWh = 1 token with 18 decimals)
        uint256 tokenAmount = amount * 10**decimals();

        _mint(to, tokenAmount);

        totalEnergyProduced[to] += amount;

        emit EnergyMinted(to, amount, metadata);
    }

    /**
     * @dev Record energy purchase (transfer between seller and buyer)
     * This is called by the platform after payment is confirmed
     * @param seller Address of the energy seller
     * @param buyer Address of the energy buyer
     * @param amount Amount of energy in kWh
     * @param price Price paid in wei (ETH)
     */
    function recordPurchase(
        address seller,
        address buyer,
        uint256 amount,
        uint256 price
    ) public onlyOwner {
        require(seller != address(0), "Invalid seller address");
        require(buyer != address(0), "Invalid buyer address");
        require(amount > 0, "Amount must be greater than zero");

        uint256 tokenAmount = amount * 10**decimals();

        // Transfer tokens from seller to buyer
        _transfer(seller, buyer, tokenAmount);

        emit EnergyPurchased(buyer, seller, amount, price);
    }

    /**
     * @dev Burn tokens when energy is consumed
     * @param amount Amount of energy consumed in kWh
     */
    function consumeEnergy(uint256 amount) public {
        require(amount > 0, "Amount must be greater than zero");

        uint256 tokenAmount = amount * 10**decimals();

        // Burn tokens from caller's balance
        burn(tokenAmount);

        totalEnergyConsumed[msg.sender] += amount;

        emit EnergyConsumed(msg.sender, amount);
    }

    /**
     * @dev Get token balance in kWh (human-readable format)
     * @param account Address to check balance
     * @return Balance in kWh
     */
    function getEnergyBalance(address account) public view returns (uint256) {
        return balanceOf(account) / 10**decimals();
    }

    /**
     * @dev Get total energy produced by a seller
     * @param seller Address of the seller
     * @return Total kWh produced
     */
    function getEnergyProduced(address seller) public view returns (uint256) {
        return totalEnergyProduced[seller];
    }

    /**
     * @dev Get total energy consumed by a buyer
     * @param buyer Address of the buyer
     * @return Total kWh consumed
     */
    function getEnergyConsumed(address buyer) public view returns (uint256) {
        return totalEnergyConsumed[buyer];
    }
}

