module clock (
    input CLK,
    input RESET,
    output clk,
    output resetn
);
    parameter SLOW=0;

    reg [SLOW:0] slow_CLK = 0;
    always @(posedge CLK) begin
        slow_CLK <= slow_CLK + 1'b1;
    end
    assign clk = slow_CLK[SLOW];
    assign resetn = ~RESET;

endmodule